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
            page.insert_text(
                (xs[col_index] + 6, ys[row_index] + 18),
                text,
                fontsize=10,
            )


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=420, height=320)
    first.insert_text((60, 50), "Financial summary")
    _draw_table(first, 60, 80)
    second = pdf.new_page(width=420, height=320)
    second.insert_text((60, 50), "No table on this page")
    return pdf.tobytes()


def _upload_pdf(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("tables.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def test_parse_document_tables(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        render_response = client.post(f"/api/documents/{document['id']}/render")
        assert render_response.status_code == 200

        parse_response = client.post(f"/api/documents/{document['id']}/parse-tables")
        assert parse_response.status_code == 200
        tables = parse_response.json()

        assert len(tables) == 1
        table = tables[0]
        assert table["node_type"] == "table"
        assert table["page_number"] == 1
        assert table["reading_order"] == 1
        assert table["bbox"] == [60.0, 80.0, 330.0, 164.0]
        assert table["metadata"]["row_count"] == 3
        assert table["metadata"]["col_count"] == 3
        assert table["metadata"]["matrix"][0] == ["Metric", "2025", "2026"]
        assert len(table["metadata"]["cells"]) == 9
        assert "Revenue\t100\t128" in table["text"]

        status_response = client.get(f"/api/documents/{document['id']}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "tables_parsed"

        list_response = client.get(f"/api/documents/{document['id']}/tables")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1
    finally:
        _reset_client()


def test_list_page_tables(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        client.post(f"/api/documents/{document['id']}/render")
        client.post(f"/api/documents/{document['id']}/parse-tables")

        first_page_response = client.get(f"/api/documents/{document['id']}/pages/1/tables")
        second_page_response = client.get(f"/api/documents/{document['id']}/pages/2/tables")

        assert first_page_response.status_code == 200
        assert len(first_page_response.json()) == 1
        assert second_page_response.status_code == 200
        assert second_page_response.json() == []
    finally:
        _reset_client()


def test_parse_tables_requires_rendered_pages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)

        response = client.post(f"/api/documents/{document['id']}/parse-tables")

        assert response.status_code == 409
        assert response.json()["detail"] == "Render pages before parsing tables"
    finally:
        _reset_client()
