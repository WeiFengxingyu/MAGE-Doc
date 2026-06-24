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
        files={"file": ("retrieval.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_search_text_and_table_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)

        text_response = client.get(
            f"/api/documents/{document['id']}/search",
            params={"query": "enterprise demand", "node_types": "text_block", "top_k": 3},
        )
        assert text_response.status_code == 200
        text_payload = text_response.json()
        assert text_payload["tool_trace"]["tool_name"] == "search_evidence"
        assert text_payload["results"][0]["node"]["node_type"] == "text_block"
        assert "enterprise" in text_payload["results"][0]["matched_terms"]
        assert text_payload["results"][0]["retrieval_source"] == "hybrid"
        assert "lexical" in text_payload["results"][0]["candidate_sources"]
        assert "semantic" in text_payload["results"][0]["score_breakdown"]

        table_response = client.get(
            f"/api/documents/{document['id']}/search",
            params={"query": "Revenue 2026", "node_types": "table", "top_k": 3},
        )
        assert table_response.status_code == 200
        table_payload = table_response.json()
        assert table_payload["results"][0]["node"]["node_type"] == "table"
        assert table_payload["results"][0]["node"]["metadata"]["matrix"][1] == [
            "Revenue",
            "100",
            "128",
        ]
        assert "metadata" in table_payload["results"][0]["candidate_sources"]
        assert table_payload["results"][0]["score_breakdown"]["metadata"] > 0
    finally:
        _reset_client()


def test_inspect_page_and_read_table_tools(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)

        inspect_response = client.get(f"/api/documents/{document['id']}/tools/inspect-page/1")
        assert inspect_response.status_code == 200
        inspect_payload = inspect_response.json()
        assert inspect_payload["tool_trace"]["tool_name"] == "inspect_page"
        assert inspect_payload["evidence_count"] >= 2
        assert inspect_payload["image_url"].endswith("/pages/1/image")

        tables = client.get(f"/api/documents/{document['id']}/tables").json()
        table_id = tables[0]["id"]
        table_response = client.get(f"/api/documents/{document['id']}/tools/read-table/{table_id}")
        assert table_response.status_code == 200
        table_payload = table_response.json()
        assert table_payload["tool_trace"]["tool_name"] == "read_table"
        assert table_payload["row_count"] == 3
        assert table_payload["col_count"] == 3
        assert table_payload["matrix"][0] == ["Metric", "2025", "2026"]
        assert len(table_payload["cells"]) == 9
    finally:
        _reset_client()


def test_verify_answer_tool(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        result = client.get(
            f"/api/documents/{document['id']}/search",
            params={"query": "Revenue 2026", "top_k": 1},
        ).json()["results"][0]
        node_id = result["node"]["id"]

        passed_response = client.post(
            f"/api/documents/{document['id']}/tools/verify-answer",
            json={
                "answer": "Revenue reached 128 in 2026.",
                "citation_node_ids": [node_id],
            },
        )
        assert passed_response.status_code == 200
        passed_payload = passed_response.json()
        assert passed_payload["passed"] is True
        assert passed_payload["covered_citation_node_ids"] == [node_id]

        failed_response = client.post(
            f"/api/documents/{document['id']}/tools/verify-answer",
            json={"answer": "", "citation_node_ids": ["missing"]},
        )
        assert failed_response.status_code == 200
        failed_payload = failed_response.json()
        assert failed_payload["passed"] is False
        assert failed_payload["missing_citation_node_ids"] == ["missing"]
    finally:
        _reset_client()
