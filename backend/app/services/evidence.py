import json
from pathlib import Path
from typing import Any

import fitz
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document
from app.models.evidence import EvidenceNode
from app.models.page import Page
from app.services.documents import get_document
from app.services.pages import get_page

TEXT_NODE_TYPE = "text_block"
TABLE_NODE_TYPE = "table"


def _json_loads(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _node_to_response(node: EvidenceNode) -> dict:
    return {
        "id": node.id,
        "document_id": node.document_id,
        "page_id": node.page_id,
        "page_number": node.page.page_number,
        "node_type": node.node_type,
        "text": node.text,
        "bbox": _json_loads(node.bbox_json, []),
        "reading_order": node.reading_order,
        "metadata": _json_loads(node.metadata_json, {}),
        "created_at": node.created_at,
    }


def _page_records(db: Session, document_id: str) -> list[Page]:
    return (
        db.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_number.asc())
        .all()
    )


def _text_nodes_query(db: Session, document_id: str):
    return _typed_nodes_query(db, document_id, TEXT_NODE_TYPE)


def _typed_nodes_query(db: Session, document_id: str, node_type: str):
    return (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.node_type == node_type,
        )
        .order_by(EvidenceNode.reading_order.asc())
    )


def parse_document_text_blocks(db: Session, document_id: str) -> list[dict]:
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

    pages = _page_records(db, document_id)
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Render pages before parsing text blocks",
        )
    page_by_number = {page.page_number: page for page in pages}

    try:
        with fitz.open(pdf_path) as pdf:
            if len(pages) != pdf.page_count:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Rendered page records are out of sync with the PDF",
                )

            document.status = "parsing"
            document.error_message = None
            db.commit()

            db.query(EvidenceNode).filter(
                EvidenceNode.document_id == document_id,
                EvidenceNode.node_type == TEXT_NODE_TYPE,
            ).delete(synchronize_session=False)

            nodes: list[EvidenceNode] = []
            reading_order = 1
            for page_number, pdf_page in enumerate(pdf, start=1):
                page = page_by_number[page_number]
                blocks = pdf_page.get_text("blocks", sort=True)
                for block in blocks:
                    if len(block) < 5:
                        continue
                    block_type = int(block[6]) if len(block) > 6 else 0
                    if block_type != 0:
                        continue
                    text = str(block[4]).strip()
                    if not text:
                        continue

                    bbox = [float(block[0]), float(block[1]), float(block[2]), float(block[3])]
                    lines = [line for line in text.splitlines() if line.strip()]
                    metadata = {
                        "source": "pymupdf",
                        "method": "page.get_text(blocks)",
                        "block_no": int(block[5]) if len(block) > 5 else None,
                        "block_type": block_type,
                        "line_count": len(lines),
                    }
                    node = EvidenceNode(
                        document_id=document_id,
                        page_id=page.id,
                        node_type=TEXT_NODE_TYPE,
                        text=text,
                        bbox_json=json.dumps(bbox),
                        reading_order=reading_order,
                        metadata_json=json.dumps(metadata),
                    )
                    db.add(node)
                    nodes.append(node)
                    reading_order += 1

            document.status = "parsed"
            document.error_message = None
            db.commit()

            for node in nodes:
                db.refresh(node)
            return [_node_to_response(node) for node in nodes]
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "failed"
            document.error_message = f"Text parsing failed: {exc}"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text parsing failed",
        ) from exc


def _table_text(matrix: list[list[str | None]]) -> str:
    rows: list[str] = []
    for row in matrix:
        normalized = [str(cell or "").replace("\n", " ").strip() for cell in row]
        rows.append("\t".join(normalized))
    return "\n".join(rows)


def _normalize_cell(cell: Any) -> list[float] | None:
    if cell is None:
        return None
    if hasattr(cell, "x0"):
        return [float(cell.x0), float(cell.y0), float(cell.x1), float(cell.y1)]
    if isinstance(cell, (list, tuple)) and len(cell) == 4:
        return [float(cell[0]), float(cell[1]), float(cell[2]), float(cell[3])]
    return None


def parse_document_tables(db: Session, document_id: str) -> list[dict]:
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

    pages = _page_records(db, document_id)
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Render pages before parsing tables",
        )
    page_by_number = {page.page_number: page for page in pages}

    try:
        with fitz.open(pdf_path) as pdf:
            if len(pages) != pdf.page_count:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Rendered page records are out of sync with the PDF",
                )

            document.status = "parsing_tables"
            document.error_message = None
            db.commit()

            db.query(EvidenceNode).filter(
                EvidenceNode.document_id == document_id,
                EvidenceNode.node_type == TABLE_NODE_TYPE,
            ).delete(synchronize_session=False)

            nodes: list[EvidenceNode] = []
            reading_order = 1
            for page_number, pdf_page in enumerate(pdf, start=1):
                page = page_by_number[page_number]
                finder = pdf_page.find_tables()
                for table_index, table in enumerate(finder.tables, start=1):
                    matrix = table.extract()
                    bbox = [float(value) for value in table.bbox]
                    cells = [
                        normalized
                        for normalized in (_normalize_cell(cell) for cell in table.cells)
                        if normalized is not None
                    ]
                    metadata = {
                        "source": "pymupdf",
                        "method": "page.find_tables",
                        "table_index": table_index,
                        "row_count": int(table.row_count),
                        "col_count": int(table.col_count),
                        "cells": cells,
                        "matrix": matrix,
                    }
                    node = EvidenceNode(
                        document_id=document_id,
                        page_id=page.id,
                        node_type=TABLE_NODE_TYPE,
                        text=_table_text(matrix),
                        bbox_json=json.dumps(bbox),
                        reading_order=reading_order,
                        metadata_json=json.dumps(metadata),
                    )
                    db.add(node)
                    nodes.append(node)
                    reading_order += 1

            document.status = "tables_parsed"
            document.error_message = None
            db.commit()

            for node in nodes:
                db.refresh(node)
            return [_node_to_response(node) for node in nodes]
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document is not None:
            document.status = "failed"
            document.error_message = f"Table parsing failed: {exc}"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Table parsing failed",
        ) from exc


def list_document_text_blocks(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    return [_node_to_response(node) for node in _text_nodes_query(db, document_id).all()]


def list_document_tables(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    return [_node_to_response(node) for node in _typed_nodes_query(db, document_id, TABLE_NODE_TYPE).all()]


def list_page_text_blocks(db: Session, document_id: str, page_number: int) -> list[dict]:
    return _list_page_nodes(db, document_id, page_number, TEXT_NODE_TYPE)


def list_page_tables(db: Session, document_id: str, page_number: int) -> list[dict]:
    return _list_page_nodes(db, document_id, page_number, TABLE_NODE_TYPE)


def _list_page_nodes(db: Session, document_id: str, page_number: int, node_type: str) -> list[dict]:
    page = get_page(db, document_id, page_number)
    nodes = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.page_id == page.id,
            EvidenceNode.node_type == node_type,
        )
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )
    return [_node_to_response(node) for node in nodes]
