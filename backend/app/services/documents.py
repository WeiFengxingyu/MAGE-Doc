from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document

ALLOWED_CONTENT_TYPES = {"", "application/pdf", "application/octet-stream"}
CHUNK_SIZE = 1024 * 1024


def _is_pdf_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() == ".pdf"


def _document_dir(document_id: str) -> Path:
    return settings.upload_root / document_id


def list_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_document(db: Session, document_id: str) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


async def create_document(db: Session, file: UploadFile) -> Document:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    if not _is_pdf_filename(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF uploads are supported",
        )

    document = Document(
        filename=file.filename,
        stored_filename="original.pdf",
        file_path="",
        content_type=content_type,
        file_size=0,
        page_count=None,
        status="uploaded",
    )
    db.add(document)
    db.flush()

    target_dir = _document_dir(document.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / document.stored_filename

    total_size = 0
    try:
        with target_path.open("wb") as output:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.upload_max_bytes:
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Uploaded PDF exceeds the configured size limit",
                    )
                output.write(chunk)
    finally:
        await file.close()

    if total_size == 0:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF is empty",
        )

    document.file_size = total_size
    document.file_path = str(target_path)
    db.commit()
    db.refresh(document)
    return document
