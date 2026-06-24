from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.documents import get_document
from app.services.evidence import parse_document_tables, parse_document_text_blocks
from app.services.pages import render_document_pages


def prepare_document_demo(db: Session, document_id: str) -> dict:
    document = get_document(db, document_id)
    document.status = "preparing_demo"
    document.error_message = None
    db.commit()

    steps: list[dict] = []
    try:
        pages = render_document_pages(db, document_id)
        steps.append(
            {
                "name": "render_pages",
                "status": "ok",
                "output_summary": f"{len(pages)} pages",
            }
        )

        text_blocks = parse_document_text_blocks(db, document_id)
        steps.append(
            {
                "name": "parse_text_blocks",
                "status": "ok",
                "output_summary": f"{len(text_blocks)} text blocks",
            }
        )

        tables = parse_document_tables(db, document_id)
        steps.append(
            {
                "name": "parse_tables",
                "status": "ok",
                "output_summary": f"{len(tables)} tables",
            }
        )

        document = get_document(db, document_id)
        document.status = "demo_ready"
        document.error_message = None
        db.commit()

        return {
            "document_id": document_id,
            "status": "demo_ready",
            "page_count": len(pages),
            "text_block_count": len(text_blocks),
            "table_count": len(tables),
            "steps": steps,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "failed"
            document.error_message = f"Prepare demo failed: {exc}"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prepare demo failed",
        ) from exc
