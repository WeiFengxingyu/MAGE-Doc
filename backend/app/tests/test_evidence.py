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
    first.insert_text((72, 82), "Revenue increased in 2026")
    first.insert_text((72, 128), "Operating margin improved")
    second = pdf.new_page(width=320, height=420)
    second.insert_text((72, 82), "Risk factors changed by region")
    return pdf.tobytes()


def _upload_pdf(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("report.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def test_parse_document_text_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        render_response = client.post(f"/api/documents/{document['id']}/render")
        assert render_response.status_code == 200

        parse_response = client.post(f"/api/documents/{document['id']}/parse-text")
        assert parse_response.status_code == 200
        nodes = parse_response.json()

        assert len(nodes) >= 2
        assert [node["reading_order"] for node in nodes] == list(range(1, len(nodes) + 1))
        assert {node["node_type"] for node in nodes} == {"text_block"}
        assert all(len(node["bbox"]) == 4 for node in nodes)
        assert all(node["metadata"]["source"] == "pymupdf" for node in nodes)
        assert "Revenue increased" in "\n".join(node["text"] for node in nodes)

        status_response = client.get(f"/api/documents/{document['id']}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "parsed"

        list_response = client.get(f"/api/documents/{document['id']}/text-blocks")
        assert list_response.status_code == 200
        assert len(list_response.json()) == len(nodes)
    finally:
        _reset_client()


def test_list_page_text_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)
        client.post(f"/api/documents/{document['id']}/render")
        client.post(f"/api/documents/{document['id']}/parse-text")

        response = client.get(f"/api/documents/{document['id']}/pages/2/text-blocks")

        assert response.status_code == 200
        nodes = response.json()
        assert len(nodes) >= 1
        assert {node["page_number"] for node in nodes} == {2}
        assert "Risk factors" in "\n".join(node["text"] for node in nodes)
    finally:
        _reset_client()


def test_parse_requires_rendered_pages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        document = _upload_pdf(client)

        response = client.post(f"/api/documents/{document['id']}/parse-text")

        assert response.status_code == 409
        assert response.json()["detail"] == "Render pages before parsing text blocks"
    finally:
        _reset_client()
