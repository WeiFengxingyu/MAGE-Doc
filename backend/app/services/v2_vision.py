import json
import time
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.models.page import Page
from app.services.documents import get_document
from app.services.evidence import TABLE_NODE_TYPE, _node_to_response
from app.services.graph import PHASE2_GRAPH_SOURCE, upsert_edge

CHART_NODE_TYPE = "chart"
FIGURE_NODE_TYPE = "figure"
VISUAL_SUMMARY_NODE_TYPE = "visual_summary"
VISION_SOURCE = "v2_mock_vision_grounding"


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _bbox_from_page(page: Page) -> list[float]:
    return [48.0, 72.0, max(120.0, page.width - 48.0), min(page.height - 48.0, 220.0)]


def run_vision_grounding(db: Session, document_id: str) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    db.query(EvidenceNode).filter(
        EvidenceNode.document_id == document_id,
        EvidenceNode.node_type.in_([CHART_NODE_TYPE, FIGURE_NODE_TYPE, VISUAL_SUMMARY_NODE_TYPE]),
    ).delete(synchronize_session=False)
    pages = (
        db.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_number.asc())
        .all()
    )
    created_edges = 0
    nodes: list[EvidenceNode] = []
    for page in pages:
        tables = (
            db.query(EvidenceNode)
            .filter(EvidenceNode.page_id == page.id, EvidenceNode.node_type == TABLE_NODE_TYPE)
            .all()
        )
        if not tables:
            continue
        chart = EvidenceNode(
            document_id=document_id,
            page_id=page.id,
            node_type=CHART_NODE_TYPE,
            text=f"Chart candidate on page {page.page_number}",
            bbox_json=json.dumps(_bbox_from_page(page)),
            reading_order=950000 + page.page_number * 100,
            metadata_json=json.dumps({"source": VISION_SOURCE, "page_number": page.page_number}),
        )
        db.add(chart)
        db.flush()
        summary = EvidenceNode(
            document_id=document_id,
            page_id=page.id,
            node_type=VISUAL_SUMMARY_NODE_TYPE,
            text=f"Visual summary: chart on page {page.page_number} appears related to table metrics.",
            bbox_json=json.dumps(_bbox_from_page(page)),
            reading_order=950000 + page.page_number * 100 + 1,
            metadata_json=json.dumps(
                {
                    "source": VISION_SOURCE,
                    "adapter": "mock",
                    "chart_node_id": chart.id,
                    "page_number": page.page_number,
                }
            ),
        )
        db.add(summary)
        db.flush()
        nodes.extend([chart, summary])
        _, created = upsert_edge(
            db,
            document_id=document_id,
            source_node_id=summary.id,
            target_node_id=chart.id,
            edge_type="derived_from",
            source=VISION_SOURCE,
            metadata={"reason": "visual_summary_describes_chart"},
        )
        created_edges += int(created)
        for table in tables:
            _, created = upsert_edge(
                db,
                document_id=document_id,
                source_node_id=chart.id,
                target_node_id=table.id,
                edge_type="visualizes",
                source=VISION_SOURCE,
                metadata={"reason": "mock_chart_near_table"},
            )
            created_edges += int(created)
    db.commit()
    for node in nodes:
        db.refresh(node)
    return {
        "document_id": document_id,
        "visual_node_count": len(nodes),
        "created_edge_count": created_edges,
        "nodes": [_node_to_response(node) for node in nodes],
        "tool_trace": _trace(
            "run_vision_grounding",
            {"document_id": document_id},
            f"{len(nodes)} visual nodes",
            start,
        ),
    }


def list_visual_nodes(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    nodes = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.node_type.in_([CHART_NODE_TYPE, FIGURE_NODE_TYPE, VISUAL_SUMMARY_NODE_TYPE]),
        )
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )
    return [_node_to_response(node) for node in nodes]
