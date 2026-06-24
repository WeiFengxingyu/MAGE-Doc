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
    col_widths = [80, 80]
    row_heights = [26, 26]
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
    values = [["Metric", "2026"], ["Revenue", "128"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 17), text, fontsize=10)


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    page = pdf.new_page(width=420, height=360)
    page.insert_text((60, 30), "1. Financial Highlights")
    page.insert_text((60, 65), "Table 1. Revenue summary")
    _draw_table(page, 60, 90)
    page.insert_text((60, 170), "Revenue increased due to enterprise demand.")
    second = pdf.new_page(width=420, height=360)
    second.insert_text((60, 40), "Risk factors include supply chain delays.")
    return pdf.tobytes()


def _upload_parse_tables(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("pack.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_evidence_pack_depth_zero_returns_source_candidates_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_parse_tables(client)
        response = client.get(
            f"/api/documents/{document['id']}/evidence-pack",
            params={"query": "enterprise demand", "top_k": 1, "depth": 0},
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["tool_trace"]["tool_name"] == "build_evidence_pack"
        assert payload["summary"]["source_candidate_count"] == 1
        assert payload["summary"]["max_graph_distance"] == 0
        assert len(payload["items"]) == 1
        assert payload["items"][0]["inclusion_reason"] == "source_candidate"
        assert payload["items"][0]["path"] == []
    finally:
        _reset_client()


def test_evidence_pack_expands_table_context_with_cells_and_caption(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_parse_tables(client)
        response = client.get(
            f"/api/documents/{document['id']}/evidence-pack",
            params={"query": "Revenue 2026 table", "top_k": 1, "depth": 1, "node_types": "table"},
        )
        assert response.status_code == 200
        payload = response.json()

        node_types = {item["node"]["node_type"] for item in payload["items"]}
        reasons = {item["inclusion_reason"] for item in payload["items"]}
        assert "table" in node_types
        assert "table_cell" in node_types
        assert "caption" in node_types
        assert "table_structure_context" in reasons
        assert "caption_context" in reasons
        assert payload["summary"]["edge_type_counts"]["part_of"] >= 1
        assert payload["summary"]["edge_type_counts"]["caption_of"] >= 1
        assert payload["summary"]["max_graph_distance"] == 1
    finally:
        _reset_client()
