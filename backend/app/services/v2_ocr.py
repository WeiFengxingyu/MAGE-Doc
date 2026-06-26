import json
import time
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.models.page import Page
from app.models.v2 import OcrRun
from app.services.documents import get_document
from app.services.evidence import _json_loads, _node_to_response

OCR_NODE_TYPE = "ocr_text_block"


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _run_to_response(run: OcrRun) -> dict:
    return {
        "id": run.id,
        "document_id": run.document_id,
        "page_id": run.page_id,
        "page_number": run.page_number,
        "status": run.status,
        "adapter": run.adapter,
        "text_block_count": run.text_block_count,
        "average_confidence": run.average_confidence,
        "metadata": _json_loads(run.metadata_json, {}),
        "created_at": run.created_at,
    }


def _page_text_stats(db: Session, page: Page) -> tuple[int, int]:
    nodes = (
        db.query(EvidenceNode)
        .filter(EvidenceNode.page_id == page.id, EvidenceNode.node_type == "text_block")
        .all()
    )
    return len(nodes), sum(len(node.text.strip()) for node in nodes)


def _mock_ocr_blocks(page: Page) -> list[dict[str, Any]]:
    return [
        {
            "text": f"Mock OCR text for scanned page {page.page_number}",
            "bbox": [48.0, 48.0, max(120.0, page.width - 48.0), 86.0],
            "confidence": 0.91,
        }
    ]


def _upsert_ocr_run(
    db: Session,
    *,
    document_id: str,
    page: Page,
    status: str,
    block_count: int,
    average_confidence: float,
    metadata: dict[str, Any],
) -> OcrRun:
    run = (
        db.query(OcrRun)
        .filter(OcrRun.document_id == document_id, OcrRun.page_id == page.id)
        .one_or_none()
    )
    if run is None:
        run = OcrRun(document_id=document_id, page_id=page.id, page_number=page.page_number)
        db.add(run)
    run.status = status
    run.adapter = "mock"
    run.text_block_count = block_count
    run.average_confidence = average_confidence
    run.metadata_json = json.dumps(metadata)
    return run


def run_document_ocr(db: Session, document_id: str, min_text_chars: int = 20) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    pages = (
        db.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_number.asc())
        .all()
    )
    db.query(EvidenceNode).filter(
        EvidenceNode.document_id == document_id,
        EvidenceNode.node_type == OCR_NODE_TYPE,
    ).delete(synchronize_session=False)
    runs: list[OcrRun] = []
    nodes: list[EvidenceNode] = []
    reading_order = 900000
    for page in pages:
        text_block_count, text_char_count = _page_text_stats(db, page)
        should_ocr = text_char_count < min_text_chars
        if not should_ocr:
            runs.append(
                _upsert_ocr_run(
                    db,
                    document_id=document_id,
                    page=page,
                    status="skipped",
                    block_count=0,
                    average_confidence=0.0,
                    metadata={
                        "reason": "page_has_sufficient_text",
                        "text_block_count": text_block_count,
                        "text_char_count": text_char_count,
                        "min_text_chars": min_text_chars,
                    },
                )
            )
            continue
        blocks = _mock_ocr_blocks(page)
        confidences = [float(block["confidence"]) for block in blocks]
        average_confidence = sum(confidences) / max(len(confidences), 1)
        runs.append(
            _upsert_ocr_run(
                db,
                document_id=document_id,
                page=page,
                status="completed",
                block_count=len(blocks),
                average_confidence=average_confidence,
                metadata={
                    "reason": "low_text_density",
                    "text_block_count": text_block_count,
                    "text_char_count": text_char_count,
                    "min_text_chars": min_text_chars,
                },
            )
        )
        for index, block in enumerate(blocks, start=1):
            node = EvidenceNode(
                document_id=document_id,
                page_id=page.id,
                node_type=OCR_NODE_TYPE,
                text=str(block["text"]),
                bbox_json=json.dumps(block["bbox"]),
                reading_order=reading_order + page.page_number * 100 + index,
                metadata_json=json.dumps(
                    {
                        "source": "mock_ocr",
                        "confidence": block["confidence"],
                        "page_number": page.page_number,
                    }
                ),
            )
            db.add(node)
            nodes.append(node)
    db.commit()
    for run in runs:
        db.refresh(run)
    for node in nodes:
        db.refresh(node)
    return {
        "document_id": document_id,
        "page_count": len(pages),
        "ocr_run_count": len(runs),
        "ocr_text_block_count": len(nodes),
        "runs": [_run_to_response(run) for run in runs],
        "nodes": [_node_to_response(node) for node in nodes],
        "tool_trace": _trace(
            "run_ocr",
            {"document_id": document_id, "min_text_chars": min_text_chars},
            f"{len(nodes)} ocr text blocks",
            start,
        ),
    }


def list_ocr_runs(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    runs = (
        db.query(OcrRun)
        .filter(OcrRun.document_id == document_id)
        .order_by(OcrRun.page_number.asc())
        .all()
    )
    return [_run_to_response(run) for run in runs]


def list_ocr_text_blocks(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    nodes = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id, EvidenceNode.node_type == OCR_NODE_TYPE)
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )
    return [_node_to_response(node) for node in nodes]
