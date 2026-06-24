from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app


def _client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'test.sqlite'}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _reset_client() -> None:
    app.dependency_overrides.clear()


def _draw_table(page: fitz.Page, x0: float, y0: float) -> None:
    col_widths = [90, 90, 90]
    row_heights = [28, 28, 28]
    xs = [x0]
    for width in col_widths:
        xs.append(xs[-1] + width)
    ys = [y0]
    for height in row_heights:
        ys.append(ys[-1] + height)
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), color=(0, 0, 0), width=0.8)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), color=(0, 0, 0), width=0.8)
    values = [["Metric", "2025", "2026"], ["Revenue", "100", "128"], ["Margin", "18%", "22%"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=420, height=320)
    first.insert_text((60, 50), "Revenue increased because enterprise demand improved.")
    _draw_table(first, 60, 95)
    return pdf.tobytes()


def _upload_and_parse(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("trace.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_tool_registry_lists_agent_tools(tmp_path: Path) -> None:
    client = _client(tmp_path)
    try:
        response = client.get("/api/tools")
        assert response.status_code == 200
        tools = response.json()
        tool_names = {tool["name"] for tool in tools}
        assert {
            "search_evidence",
            "inspect_page",
            "read_table",
            "verify_answer",
            "build_evidence_pack",
        }.issubset(tool_names)
    finally:
        _reset_client()


def test_question_trace_is_persisted_and_queryable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        response = client.post(
            f"/api/documents/{document['id']}/questions",
            json={"question": "What was revenue in 2026?"},
        )
        assert response.status_code == 200
        answer = response.json()
        trace_id = answer["trace_id"]
        assert trace_id

        list_response = client.get(f"/api/documents/{document['id']}/traces")
        assert list_response.status_code == 200
        traces = list_response.json()
        assert traces[0]["id"] == trace_id
        assert traces[0]["status"] == "completed"
        assert traces[0]["tool_call_count"] == 3

        detail_response = client.get(f"/api/documents/{document['id']}/traces/{trace_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert [call["tool_name"] for call in detail["tool_calls"]] == [
            "search_evidence",
            "read_table",
            "verify_answer",
        ]
        assert [call["step_index"] for call in detail["tool_calls"]] == [1, 2, 3]
    finally:
        _reset_client()


def test_no_evidence_question_still_persists_verify_trace(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        response = client.post(
            f"/api/documents/{document['id']}/questions",
            json={"question": "unfindable xenoterm"},
        )
        assert response.status_code == 200
        trace_id = response.json()["trace_id"]

        detail = client.get(f"/api/documents/{document['id']}/traces/{trace_id}").json()
        assert detail["status"] == "completed"
        assert detail["metadata"]["result"] == "no_supporting_evidence"
        assert detail["tool_calls"][-1]["tool_name"] == "verify_answer"
    finally:
        _reset_client()
