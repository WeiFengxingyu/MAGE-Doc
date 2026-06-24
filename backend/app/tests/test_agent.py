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

    values = [
        ["Metric", "2025", "2026"],
        ["Revenue", "100", "128"],
        ["Margin", "18%", "22%"],
    ]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=420, height=320)
    first.insert_text((60, 50), "Revenue increased because enterprise demand improved.")
    _draw_table(first, 60, 95)
    second = pdf.new_page(width=420, height=320)
    second.insert_text((60, 50), "Risk factors include supply chain delays.")
    return pdf.tobytes()


def _upload_and_parse(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("agent.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_table_question_runs_agentic_rag_loop(tmp_path: Path, monkeypatch) -> None:
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
        payload = response.json()
        assert payload["question_type"] == "table_lookup"
        assert payload["citations"][0]["node_type"] == "table"
        assert "Revenue | 100 | 128" in payload["answer"]
        assert payload["verification"]["passed"] is True
        assert [trace["tool_name"] for trace in payload["trace"]] == [
            "search_evidence",
            "read_table",
            "verify_answer",
        ]
    finally:
        _reset_client()


def test_text_question_runs_agentic_rag_loop(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        response = client.post(
            f"/api/documents/{document['id']}/questions",
            json={"question": "What explains enterprise demand?"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["question_type"] == "text_lookup"
        assert payload["citations"][0]["node_type"] == "text_block"
        assert "enterprise demand" in payload["answer"].lower()
        assert payload["verification"]["passed"] is True
        assert [trace["tool_name"] for trace in payload["trace"]] == [
            "search_evidence",
            "inspect_page",
            "verify_answer",
        ]
    finally:
        _reset_client()


def test_question_requires_text(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        response = client.post(
            f"/api/documents/{document['id']}/questions",
            json={"question": " "},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Question is required"
    finally:
        _reset_client()


def test_question_without_matching_evidence_returns_empty_citations(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
        payload = response.json()
        assert payload["citations"] == []
        assert payload["verification"]["passed"] is False
        assert payload["trace"][-1]["tool_name"] == "verify_answer"
    finally:
        _reset_client()
