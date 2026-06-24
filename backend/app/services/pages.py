from pathlib import Path

import fitz
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.page import Page
from app.services.documents import get_document


def _page_image_dir(document_id: str) -> Path:
    return settings.page_image_root / document_id


def _page_image_path(document_id: str, page_number: int) -> Path:
    return _page_image_dir(document_id) / f"page-{page_number:04d}.png"


def _page_to_response(page: Page) -> dict:
    return {
        "id": page.id,
        "document_id": page.document_id,
        "page_number": page.page_number,
        "width": page.width,
        "height": page.height,
        "image_width": page.image_width,
        "image_height": page.image_height,
        "image_url": f"/api/documents/{page.document_id}/pages/{page.page_number}/image",
        "created_at": page.created_at,
    }


def list_pages(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    pages = (
        db.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_number.asc())
        .all()
    )
    return [_page_to_response(page) for page in pages]


def get_page(db: Session, document_id: str, page_number: int) -> Page:
    page = (
        db.query(Page)
        .filter(Page.document_id == document_id, Page.page_number == page_number)
        .one_or_none()
    )
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    return page


def get_page_response(db: Session, document_id: str, page_number: int) -> dict:
    return _page_to_response(get_page(db, document_id, page_number))


def get_page_image_path(db: Session, document_id: str, page_number: int) -> Path:
    page = get_page(db, document_id, page_number)
    path = Path(page.image_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page image not found",
        )
    return path


def render_document_pages(db: Session, document_id: str) -> list[dict]:
    document = get_document(db, document_id)
    pdf_path = Path(document.file_path)
    if not pdf_path.exists():
        document.status = "failed"
        document.error_message = "Original PDF file not found"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original PDF file not found",
        )

    document.status = "rendering"
    document.error_message = None
    db.commit()

    image_dir = _page_image_dir(document_id)
    image_dir.mkdir(parents=True, exist_ok=True)

    try:
        with fitz.open(pdf_path) as pdf:
            db.query(Page).filter(Page.document_id == document_id).delete()
            pages: list[Page] = []
            matrix = fitz.Matrix(settings.render_zoom, settings.render_zoom)
            for index, pdf_page in enumerate(pdf, start=1):
                pixmap = pdf_page.get_pixmap(matrix=matrix, alpha=False)
                image_path = _page_image_path(document_id, index)
                pixmap.save(image_path)
                page = Page(
                    document_id=document_id,
                    page_number=index,
                    width=float(pdf_page.rect.width),
                    height=float(pdf_page.rect.height),
                    image_width=pixmap.width,
                    image_height=pixmap.height,
                    image_path=str(image_path),
                )
                db.add(page)
                pages.append(page)

            document.page_count = len(pages)
            document.status = "rendered"
            document.error_message = None
            db.commit()

            for page in pages:
                db.refresh(page)
            return [_page_to_response(page) for page in pages]
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "failed"
            document.error_message = f"PDF rendering failed: {exc}"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF rendering failed",
        ) from exc

