from pathlib import Path

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


def test_upload_document_and_list(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        response = client.post(
            "/api/documents",
            files={"file": ("report.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
        )
        assert response.status_code == 201
        created = response.json()
        assert created["filename"] == "report.pdf"
        assert created["file_size"] == len(b"%PDF-1.7\ncontent")
        assert created["page_count"] is None
        assert created["status"] == "uploaded"

        list_response = client.get("/api/documents")
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [created["id"]]

        stored_file = tmp_path / "uploads" / created["id"] / "original.pdf"
        assert stored_file.read_bytes() == b"%PDF-1.7\ncontent"
    finally:
        _reset_client()


def test_document_detail_and_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        created = client.post(
            "/api/documents",
            files={"file": ("manual.pdf", b"%PDF-1.7\nmanual", "application/pdf")},
        ).json()

        detail_response = client.get(f"/api/documents/{created['id']}")
        assert detail_response.status_code == 200
        assert detail_response.json()["filename"] == "manual.pdf"

        status_response = client.get(f"/api/documents/{created['id']}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "uploaded"
        assert status_response.json()["page_count"] is None
    finally:
        _reset_client()


def test_rejects_non_pdf(tmp_path: Path) -> None:
    client = _client(tmp_path)
    try:
        response = client.post(
            "/api/documents",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Only PDF files are supported"
    finally:
        _reset_client()


def test_rejects_empty_pdf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        response = client.post(
            "/api/documents",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Uploaded PDF is empty"
    finally:
        _reset_client()


def test_missing_document_returns_404(tmp_path: Path) -> None:
    client = _client(tmp_path)
    try:
        response = client.get("/api/documents/missing")
        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"
    finally:
        _reset_client()
