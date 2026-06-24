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


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=300, height=400)
    first.insert_text((72, 72), "MAGE-Doc page one")
    second = pdf.new_page(width=320, height=420)
    second.insert_text((72, 72), "MAGE-Doc page two")
    return pdf.tobytes()


def _upload_pdf(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("sample.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def test_render_document_pages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        response = client.post(f"/api/documents/{document['id']}/render")

        assert response.status_code == 200
        pages = response.json()
        assert [page["page_number"] for page in pages] == [1, 2]
        assert pages[0]["width"] == 300
        assert pages[0]["height"] == 400
        assert pages[0]["image_width"] == 600
        assert pages[0]["image_height"] == 800
        assert pages[0]["image_url"].endswith("/pages/1/image")

        status_response = client.get(f"/api/documents/{document['id']}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "rendered"
        assert status_response.json()["page_count"] == 2

        image_path = tmp_path / "page-images" / document["id"] / "page-0001.png"
        assert image_path.exists()
    finally:
        _reset_client()


def test_list_page_detail_and_image(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        client.post(f"/api/documents/{document['id']}/render")

        list_response = client.get(f"/api/documents/{document['id']}/pages")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2

        detail_response = client.get(f"/api/documents/{document['id']}/pages/2")
        assert detail_response.status_code == 200
        assert detail_response.json()["page_number"] == 2
        assert detail_response.json()["width"] == 320
        assert detail_response.json()["height"] == 420

        image_response = client.get(f"/api/documents/{document['id']}/pages/2/image")
        assert image_response.status_code == 200
        assert image_response.headers["content-type"] == "image/png"
        assert image_response.content.startswith(b"\x89PNG")
    finally:
        _reset_client()


def test_missing_page_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        client.post(f"/api/documents/{document['id']}/render")

        response = client.get(f"/api/documents/{document['id']}/pages/9")
        assert response.status_code == 404
        assert response.json()["detail"] == "Page not found"
    finally:
        _reset_client()

