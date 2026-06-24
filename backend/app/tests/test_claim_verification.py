from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app
from app.services.claim_verification import verify_claims


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
    page = pdf.new_page(width=360, height=260)
    page.insert_text((60, 60), "Revenue reached 128 in 2026.")
    return pdf.tobytes()


def _upload_document(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("claims.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def test_verify_claims_supported_text_claim(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        document = _upload_document(client)
        db = next(app.dependency_overrides[get_db]())
        payload = verify_claims(
            db,
            document["id"],
            answer="Revenue reached 128 in 2026.",
            citations=[
                {
                    "node_id": "node-1",
                    "node_type": "text_block",
                    "snippet": "Revenue reached 128 in 2026.",
                }
            ],
            question_type="text_lookup",
        )
        assert payload["status"] == "supported"
        assert payload["supported_count"] == 1
        assert payload["claims"][0]["matched_terms"]
    finally:
        _reset_client()


def test_verify_claims_partial_on_numeric_mismatch(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        document = _upload_document(client)
        db = next(app.dependency_overrides[get_db]())
        payload = verify_claims(
            db,
            document["id"],
            answer="Revenue reached 999 in 2026.",
            citations=[
                {
                    "node_id": "node-1",
                    "node_type": "table",
                    "snippet": "Revenue | 2026 | 128",
                }
            ],
            question_type="table_lookup",
        )
        assert payload["status"] == "partial"
        assert "999" in payload["claims"][0]["missing_terms"]
    finally:
        _reset_client()


def test_verify_claims_insufficient_without_citations(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    client = _client(tmp_path)
    try:
        document = _upload_document(client)
        db = next(app.dependency_overrides[get_db]())
        payload = verify_claims(
            db,
            document["id"],
            answer="Revenue reached 128 in 2026.",
            citations=[],
            question_type="text_lookup",
        )
        assert payload["status"] == "insufficient_evidence"
        assert payload["insufficient_evidence_count"] == 1
    finally:
        _reset_client()
