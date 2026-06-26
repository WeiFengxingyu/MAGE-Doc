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
    row_heights = [28, 28]
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
    values = [["Metric", "2025", "2026"], ["Revenue", "100", "128"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def _mixed_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=420, height=320)
    first.insert_text((60, 50), "Revenue increased because enterprise demand improved.")
    _draw_table(first, 60, 95)
    pdf.new_page(width=420, height=320)
    return pdf.tobytes()


def _upload_parse(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("v2.pdf", _mixed_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_v2_ocr_vision_and_metric_graph(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_parse(client)

        ocr_response = client.post(f"/api/documents/{document['id']}/ocr")
        assert ocr_response.status_code == 200
        ocr_payload = ocr_response.json()
        assert ocr_payload["ocr_text_block_count"] >= 1
        assert any(run["status"] == "completed" for run in ocr_payload["runs"])

        search_response = client.get(
            f"/api/documents/{document['id']}/search",
            params={"query": "Mock OCR scanned page", "node_types": "ocr_text_block", "top_k": 2},
        )
        assert search_response.status_code == 200
        assert search_response.json()["results"][0]["node"]["node_type"] == "ocr_text_block"

        vision_response = client.post(f"/api/documents/{document['id']}/vision-grounding")
        assert vision_response.status_code == 200
        vision_payload = vision_response.json()
        assert vision_payload["visual_node_count"] >= 2
        assert {"chart", "visual_summary"}.issubset(
            {node["node_type"] for node in vision_payload["nodes"]}
        )

        metric_response = client.post(f"/api/documents/{document['id']}/metric-graph/build")
        assert metric_response.status_code == 200
        metric_payload = metric_response.json()
        assert metric_payload["metric_value_count"] >= 2
        assert any("Revenue 2026" in node["text"] for node in metric_payload["nodes"])
    finally:
        _reset_client()


def test_v2_collection_search_across_documents(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        first = _upload_parse(client)
        second = _upload_parse(client)
        collection_response = client.post(
            "/api/collections",
            json={"name": "V2 collection", "description": "cross document test"},
        )
        assert collection_response.status_code == 201
        collection = collection_response.json()
        assert client.post(f"/api/collections/{collection['id']}/documents/{first['id']}").status_code == 200
        assert client.post(f"/api/collections/{collection['id']}/documents/{second['id']}").status_code == 200

        search_response = client.get(
            f"/api/collections/{collection['id']}/search",
            params={"query": "enterprise demand", "top_k": 5, "node_types": "text_block"},
        )
        assert search_response.status_code == 200
        payload = search_response.json()
        assert len(payload["results"]) >= 2
        assert {item["filename"] for item in payload["results"]} == {"v2.pdf"}
        assert {item["document_id"] for item in payload["results"]} == {first["id"], second["id"]}
    finally:
        _reset_client()
