import json
import math
import re
from collections import Counter
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.models.graph import EvidenceEdge
from app.services.documents import get_document
from app.services.evidence import TABLE_NODE_TYPE, TEXT_NODE_TYPE, _json_loads, _node_to_response

CONTAINS_EDGE = "contains"
NEXT_EDGE = "next"
PART_OF_EDGE = "part_of"
CAPTION_OF_EDGE = "caption_of"
NEAR_EDGE = "near"
PHASE1_GRAPH_SOURCE = "phase1_graph_builder"
PHASE2_GRAPH_SOURCE = "phase2_layout_graph_builder"
SECTION_NODE_TYPE = "section"
TABLE_CELL_NODE_TYPE = "table_cell"
CAPTION_NODE_TYPE = "caption"
HEADING_PATTERN = re.compile(r"^(\d+(\.\d+)*|[A-Z]|[IVX]+)[.)]\s+\S+")
CAPTION_PATTERN = re.compile(r"(table|caption|figure|表|图)", re.IGNORECASE)


def _edge_to_response(edge: EvidenceEdge) -> dict:
    return {
        "id": edge.id,
        "document_id": edge.document_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "edge_type": edge.edge_type,
        "weight": edge.weight,
        "source": edge.source,
        "metadata": _json_loads(edge.metadata_json, {}),
        "created_at": edge.created_at,
    }


def _document_nodes(db: Session, document_id: str) -> list[EvidenceNode]:
    return (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id)
        .order_by(EvidenceNode.page_id.asc(), EvidenceNode.reading_order.asc(), EvidenceNode.created_at.asc())
        .all()
    )


def _base_document_nodes(db: Session, document_id: str) -> list[EvidenceNode]:
    return (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.node_type.in_([TEXT_NODE_TYPE, TABLE_NODE_TYPE]),
        )
        .order_by(EvidenceNode.page_id.asc(), EvidenceNode.reading_order.asc(), EvidenceNode.created_at.asc())
        .all()
    )


def _reading_order_nodes(db: Session, document_id: str) -> list[EvidenceNode]:
    nodes = _base_document_nodes(db, document_id)
    return sorted(nodes, key=lambda node: (node.page.page_number, node.reading_order, node.created_at))


def _edge_exists(
    db: Session,
    document_id: str,
    source_node_id: str | None,
    target_node_id: str,
    edge_type: str,
    source: str,
) -> bool:
    query = db.query(EvidenceEdge.id).filter(
        EvidenceEdge.document_id == document_id,
        EvidenceEdge.target_node_id == target_node_id,
        EvidenceEdge.edge_type == edge_type,
        EvidenceEdge.source == source,
    )
    if source_node_id is None:
        query = query.filter(EvidenceEdge.source_node_id.is_(None))
    else:
        query = query.filter(EvidenceEdge.source_node_id == source_node_id)
    return query.first() is not None


def upsert_edge(
    db: Session,
    *,
    document_id: str,
    source_node_id: str | None,
    target_node_id: str,
    edge_type: str,
    weight: float = 1.0,
    source: str = PHASE1_GRAPH_SOURCE,
    metadata: dict[str, Any] | None = None,
) -> tuple[EvidenceEdge | None, bool]:
    if _edge_exists(db, document_id, source_node_id, target_node_id, edge_type, source):
        return None, False
    edge = EvidenceEdge(
        document_id=document_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        edge_type=edge_type,
        weight=weight,
        source=source,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(edge)
    return edge, True


def _edge_type_counts(edges: list[EvidenceEdge]) -> dict[str, int]:
    return dict(Counter(edge.edge_type for edge in edges))


def _bbox(node: EvidenceNode) -> list[float]:
    value = _json_loads(node.bbox_json, [])
    if isinstance(value, list) and len(value) == 4:
        return [float(item) for item in value]
    return [0.0, 0.0, 0.0, 0.0]


def _bbox_center(node: EvidenceNode) -> tuple[float, float]:
    x0, y0, x1, y1 = _bbox(node)
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def _bbox_distance(first: EvidenceNode, second: EvidenceNode) -> float:
    first_center = _bbox_center(first)
    second_center = _bbox_center(second)
    return math.dist(first_center, second_center)


def _is_section_candidate(node: EvidenceNode) -> bool:
    if node.node_type != TEXT_NODE_TYPE:
        return False
    text = " ".join(node.text.split())
    if not text or len(text) > 80:
        return False
    metadata = _json_loads(node.metadata_json, {})
    line_count = int(metadata.get("line_count") or len(node.text.splitlines()) or 1)
    if line_count > 2:
        return False
    if HEADING_PATTERN.search(text):
        return True
    if text.endswith((".", "。", "!", "！", "?", "？")):
        return False
    return len(text.split()) <= 10


def _node_identity(
    document_id: str,
    node_type: str,
    metadata: dict[str, Any],
) -> str:
    return json.dumps(
        {"document_id": document_id, "node_type": node_type, **metadata},
        ensure_ascii=False,
        sort_keys=True,
    )


def _find_generated_node(
    db: Session,
    document_id: str,
    node_type: str,
    identity: str,
) -> EvidenceNode | None:
    candidates = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.node_type == node_type,
        )
        .all()
    )
    for candidate in candidates:
        metadata = _json_loads(candidate.metadata_json, {})
        if metadata.get("identity") == identity:
            return candidate
    return None


def _get_or_create_generated_node(
    db: Session,
    *,
    document_id: str,
    page_id: str,
    node_type: str,
    text: str,
    bbox: list[float],
    reading_order: int,
    metadata: dict[str, Any],
) -> tuple[EvidenceNode, bool]:
    identity = _node_identity(document_id, node_type, metadata)
    metadata_with_identity = {
        **metadata,
        "generated_by": PHASE2_GRAPH_SOURCE,
        "identity": identity,
    }
    existing = _find_generated_node(db, document_id, node_type, identity)
    if existing is not None:
        return existing, False
    node = EvidenceNode(
        document_id=document_id,
        page_id=page_id,
        node_type=node_type,
        text=text,
        bbox_json=json.dumps(bbox),
        reading_order=reading_order,
        metadata_json=json.dumps(metadata_with_identity),
    )
    db.add(node)
    db.flush()
    db.refresh(node)
    return node, True


def _build_section_nodes_and_edges(db: Session, document_id: str, nodes: list[EvidenceNode]) -> int:
    created_edges = 0
    current_section_by_page: dict[str, EvidenceNode] = {}
    for node in nodes:
        if _is_section_candidate(node):
            section, _ = _get_or_create_generated_node(
                db,
                document_id=document_id,
                page_id=node.page_id,
                node_type=SECTION_NODE_TYPE,
                text=node.text,
                bbox=_bbox(node),
                reading_order=node.reading_order * 1000,
                metadata={
                    "source_text_node_id": node.id,
                    "page_number": node.page.page_number,
                    "rule": "short_heading_or_numbered_heading",
                },
            )
            current_section_by_page[node.page_id] = section
            _, created = upsert_edge(
                db,
                document_id=document_id,
                source_node_id=section.id,
                target_node_id=node.id,
                edge_type=CONTAINS_EDGE,
                source=PHASE2_GRAPH_SOURCE,
                metadata={
                    "container_type": SECTION_NODE_TYPE,
                    "reason": "section_candidate_contains_source_text",
                },
            )
            created_edges += int(created)
            continue

        section = current_section_by_page.get(node.page_id)
        if section is None:
            continue
        _, created = upsert_edge(
            db,
            document_id=document_id,
            source_node_id=section.id,
            target_node_id=node.id,
            edge_type=CONTAINS_EDGE,
            source=PHASE2_GRAPH_SOURCE,
            metadata={
                "container_type": SECTION_NODE_TYPE,
                "reason": "current_page_section_context",
            },
        )
        created_edges += int(created)
    return created_edges


def _cell_bbox(table_bbox: list[float], cells: list[Any], index: int) -> list[float]:
    if index < len(cells):
        cell = cells[index]
        if isinstance(cell, list) and len(cell) == 4:
            return [float(value) for value in cell]
    return table_bbox


def _build_table_cell_nodes_and_edges(db: Session, document_id: str, tables: list[EvidenceNode]) -> int:
    created_edges = 0
    for table in tables:
        metadata = _json_loads(table.metadata_json, {})
        matrix = metadata.get("matrix") if isinstance(metadata.get("matrix"), list) else []
        cells = metadata.get("cells") if isinstance(metadata.get("cells"), list) else []
        table_bbox = _bbox(table)
        cell_index = 0
        for row_index, row in enumerate(matrix):
            if not isinstance(row, list):
                continue
            for col_index, value in enumerate(row):
                cell_text = str(value or "").strip()
                if not cell_text:
                    cell_index += 1
                    continue
                cell, _ = _get_or_create_generated_node(
                    db,
                    document_id=document_id,
                    page_id=table.page_id,
                    node_type=TABLE_CELL_NODE_TYPE,
                    text=cell_text,
                    bbox=_cell_bbox(table_bbox, cells, cell_index),
                    reading_order=(table.reading_order * 10000) + (row_index * 100) + col_index,
                    metadata={
                        "table_node_id": table.id,
                        "page_number": table.page.page_number,
                        "row_index": row_index,
                        "col_index": col_index,
                        "is_header": row_index == 0,
                    },
                )
                _, created = upsert_edge(
                    db,
                    document_id=document_id,
                    source_node_id=cell.id,
                    target_node_id=table.id,
                    edge_type=PART_OF_EDGE,
                    source=PHASE2_GRAPH_SOURCE,
                    metadata={
                        "child_type": TABLE_CELL_NODE_TYPE,
                        "parent_type": TABLE_NODE_TYPE,
                        "row_index": row_index,
                        "col_index": col_index,
                    },
                )
                created_edges += int(created)
                cell_index += 1
    return created_edges


def _caption_candidate(text_node: EvidenceNode, table: EvidenceNode) -> bool:
    if text_node.page_id != table.page_id or text_node.node_type != TEXT_NODE_TYPE:
        return False
    text = " ".join(text_node.text.split())
    if not text or len(text) > 140:
        return False
    text_bbox = _bbox(text_node)
    table_bbox = _bbox(table)
    vertical_gap = min(abs(text_bbox[3] - table_bbox[1]), abs(table_bbox[3] - text_bbox[1]))
    horizontal_overlap = max(0.0, min(text_bbox[2], table_bbox[2]) - max(text_bbox[0], table_bbox[0]))
    if horizontal_overlap <= 0:
        return False
    return vertical_gap <= 60 and (CAPTION_PATTERN.search(text) is not None or len(text) <= 80)


def _build_caption_nodes_and_edges(
    db: Session,
    document_id: str,
    text_nodes: list[EvidenceNode],
    tables: list[EvidenceNode],
) -> int:
    created_edges = 0
    for table in tables:
        for text_node in text_nodes:
            if not _caption_candidate(text_node, table):
                continue
            caption, _ = _get_or_create_generated_node(
                db,
                document_id=document_id,
                page_id=text_node.page_id,
                node_type=CAPTION_NODE_TYPE,
                text=text_node.text,
                bbox=_bbox(text_node),
                reading_order=text_node.reading_order * 1000 + 1,
                metadata={
                    "source_text_node_id": text_node.id,
                    "table_node_id": table.id,
                    "page_number": text_node.page.page_number,
                    "rule": "near_table_caption_candidate",
                },
            )
            _, created = upsert_edge(
                db,
                document_id=document_id,
                source_node_id=caption.id,
                target_node_id=table.id,
                edge_type=CAPTION_OF_EDGE,
                source=PHASE2_GRAPH_SOURCE,
                metadata={
                    "caption_type": "table_caption_candidate",
                    "source_text_node_id": text_node.id,
                },
            )
            created_edges += int(created)
    return created_edges


def _build_near_edges(db: Session, document_id: str) -> int:
    created_edges = 0
    nodes = _document_nodes(db, document_id)
    nodes_by_page: dict[str, list[EvidenceNode]] = {}
    for node in nodes:
        nodes_by_page.setdefault(node.page_id, []).append(node)
    for page_nodes in nodes_by_page.values():
        for node in page_nodes:
            neighbors = [
                (round(_bbox_distance(node, candidate), 4), candidate)
                for candidate in page_nodes
                if candidate.id != node.id
            ]
            neighbors = [item for item in neighbors if item[0] <= 120]
            neighbors.sort(key=lambda item: (item[0], item[1].reading_order))
            for distance, candidate in neighbors[:3]:
                _, created = upsert_edge(
                    db,
                    document_id=document_id,
                    source_node_id=node.id,
                    target_node_id=candidate.id,
                    edge_type=NEAR_EDGE,
                    weight=max(0.1, 1 - (distance / 120)),
                    source=PHASE2_GRAPH_SOURCE,
                    metadata={"distance": distance, "page_id": node.page_id},
                )
                created_edges += int(created)
    return created_edges


def _build_layout_graph(db: Session, document_id: str, base_nodes: list[EvidenceNode]) -> int:
    text_nodes = [node for node in base_nodes if node.node_type == TEXT_NODE_TYPE]
    tables = [node for node in base_nodes if node.node_type == TABLE_NODE_TYPE]
    created_edges = 0
    created_edges += _build_section_nodes_and_edges(db, document_id, base_nodes)
    created_edges += _build_table_cell_nodes_and_edges(db, document_id, tables)
    created_edges += _build_caption_nodes_and_edges(db, document_id, text_nodes, tables)
    db.flush()
    created_edges += _build_near_edges(db, document_id)
    return created_edges


def build_document_graph(db: Session, document_id: str) -> dict:
    get_document(db, document_id)
    nodes = _reading_order_nodes(db, document_id)
    created_edge_count = 0

    for node in nodes:
        _, created = upsert_edge(
            db,
            document_id=document_id,
            source_node_id=None,
            target_node_id=node.id,
            edge_type=CONTAINS_EDGE,
            source=PHASE1_GRAPH_SOURCE,
            metadata={
                "container_type": "page",
                "page_id": node.page_id,
                "page_number": node.page.page_number,
                "target_node_type": node.node_type,
                "target_reading_order": node.reading_order,
            },
        )
        created_edge_count += int(created)

    for previous, current in zip(nodes, nodes[1:], strict=False):
        _, created = upsert_edge(
            db,
            document_id=document_id,
            source_node_id=previous.id,
            target_node_id=current.id,
            edge_type=NEXT_EDGE,
            source=PHASE1_GRAPH_SOURCE,
            metadata={
                "from_page_number": previous.page.page_number,
                "from_reading_order": previous.reading_order,
                "to_page_number": current.page.page_number,
                "to_reading_order": current.reading_order,
            },
        )
        created_edge_count += int(created)

    created_edge_count += _build_layout_graph(db, document_id, nodes)
    db.commit()
    all_nodes = _document_nodes(db, document_id)
    edges = _document_edges(db, document_id)
    return {
        "document_id": document_id,
        "node_count": len(all_nodes),
        "edge_count": len(edges),
        "created_edge_count": created_edge_count,
        "edge_type_counts": _edge_type_counts(edges),
    }


def _document_edges(db: Session, document_id: str) -> list[EvidenceEdge]:
    return (
        db.query(EvidenceEdge)
        .filter(EvidenceEdge.document_id == document_id)
        .order_by(EvidenceEdge.edge_type.asc(), EvidenceEdge.created_at.asc())
        .all()
    )


def list_document_graph(db: Session, document_id: str) -> dict:
    get_document(db, document_id)
    nodes = sorted(
        _document_nodes(db, document_id),
        key=lambda node: (node.page.page_number, node.reading_order, node.node_type, node.created_at),
    )
    edges = _document_edges(db, document_id)
    return {
        "document_id": document_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "edge_type_counts": _edge_type_counts(edges),
        "nodes": [_node_to_response(node) for node in nodes],
        "edges": [_edge_to_response(edge) for edge in edges],
    }


def get_node_neighbors(db: Session, document_id: str, node_id: str) -> dict:
    get_document(db, document_id)
    node = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id, EvidenceNode.id == node_id)
        .one_or_none()
    )
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence node not found",
        )

    edges = (
        db.query(EvidenceEdge)
        .filter(
            EvidenceEdge.document_id == document_id,
            or_(
                EvidenceEdge.source_node_id == node_id,
                EvidenceEdge.target_node_id == node_id,
            ),
        )
        .order_by(EvidenceEdge.edge_type.asc(), EvidenceEdge.created_at.asc())
        .all()
    )
    incoming_edges = [edge for edge in edges if edge.target_node_id == node_id]
    outgoing_edges = [edge for edge in edges if edge.source_node_id == node_id]
    incoming_source_ids = [
        edge.source_node_id for edge in incoming_edges if edge.source_node_id is not None
    ]
    outgoing_target_ids = [edge.target_node_id for edge in outgoing_edges]
    neighbor_ids = list(dict.fromkeys([*incoming_source_ids, *outgoing_target_ids]))
    neighbors = []
    if neighbor_ids:
        neighbors = (
            db.query(EvidenceNode)
            .options(joinedload(EvidenceNode.page))
            .filter(EvidenceNode.document_id == document_id, EvidenceNode.id.in_(neighbor_ids))
            .all()
        )
    neighbor_by_id = {neighbor.id: neighbor for neighbor in neighbors}
    return {
        "document_id": document_id,
        "node": _node_to_response(node),
        "incoming_edges": [_edge_to_response(edge) for edge in incoming_edges],
        "outgoing_edges": [_edge_to_response(edge) for edge in outgoing_edges],
        "incoming_nodes": [
            _node_to_response(neighbor_by_id[node_id])
            for node_id in incoming_source_ids
            if node_id in neighbor_by_id
        ],
        "outgoing_nodes": [
            _node_to_response(neighbor_by_id[node_id])
            for node_id in outgoing_target_ids
            if node_id in neighbor_by_id
        ],
    }
