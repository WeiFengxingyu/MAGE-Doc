import json
import re
import time
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.services.documents import get_document
from app.services.evidence import TABLE_NODE_TYPE, _json_loads, _node_to_response
from app.services.graph import upsert_edge

METRIC_VALUE_NODE_TYPE = "metric_value"
METRIC_SOURCE = "v2_metric_graph_builder"
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?%?")


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _year(value: Any) -> str | None:
    match = YEAR_PATTERN.search(str(value or ""))
    return match.group(0) if match else None


def _number(value: Any) -> str | None:
    match = NUMBER_PATTERN.search(str(value or ""))
    return match.group(0) if match else None


def build_metric_graph(db: Session, document_id: str) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    db.query(EvidenceNode).filter(
        EvidenceNode.document_id == document_id,
        EvidenceNode.node_type == METRIC_VALUE_NODE_TYPE,
    ).delete(synchronize_session=False)
    tables = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id, EvidenceNode.node_type == TABLE_NODE_TYPE)
        .all()
    )
    nodes: list[EvidenceNode] = []
    created_edges = 0
    for table in tables:
        metadata = _json_loads(table.metadata_json, {})
        matrix = metadata.get("matrix") if isinstance(metadata.get("matrix"), list) else []
        if len(matrix) < 2 or not isinstance(matrix[0], list):
            continue
        headers = matrix[0]
        years = [_year(header) for header in headers]
        for row_index, row in enumerate(matrix[1:], start=1):
            if not isinstance(row, list) or not row:
                continue
            metric_name = str(row[0] or "").strip()
            if not metric_name:
                continue
            for col_index, cell in enumerate(row[1:], start=1):
                year = years[col_index] if col_index < len(years) else None
                value = _number(cell)
                if year is None or value is None:
                    continue
                text = f"{metric_name} {year}: {value}"
                node = EvidenceNode(
                    document_id=document_id,
                    page_id=table.page_id,
                    node_type=METRIC_VALUE_NODE_TYPE,
                    text=text,
                    bbox_json=table.bbox_json,
                    reading_order=970000 + table.reading_order * 100 + row_index * 10 + col_index,
                    metadata_json=json.dumps(
                        {
                            "source": METRIC_SOURCE,
                            "metric_name": metric_name,
                            "year": year,
                            "value": value,
                            "source_table_id": table.id,
                            "row_index": row_index,
                            "col_index": col_index,
                        }
                    ),
                )
                db.add(node)
                db.flush()
                nodes.append(node)
                _, created = upsert_edge(
                    db,
                    document_id=document_id,
                    source_node_id=node.id,
                    target_node_id=table.id,
                    edge_type="derived_from",
                    source=METRIC_SOURCE,
                    metadata={"source_table_id": table.id, "metric_name": metric_name, "year": year},
                )
                created_edges += int(created)
    db.commit()
    for node in nodes:
        db.refresh(node)
    return {
        "document_id": document_id,
        "metric_value_count": len(nodes),
        "created_edge_count": created_edges,
        "nodes": [_node_to_response(node) for node in nodes],
        "tool_trace": _trace(
            "build_metric_graph",
            {"document_id": document_id},
            f"{len(nodes)} metric values",
            start,
        ),
    }


def list_metric_values(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    nodes = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id, EvidenceNode.node_type == METRIC_VALUE_NODE_TYPE)
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )
    return [_node_to_response(node) for node in nodes]
