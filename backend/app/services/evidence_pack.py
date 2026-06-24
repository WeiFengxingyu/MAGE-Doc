import time
from collections import Counter, deque
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.models.graph import EvidenceEdge
from app.services.documents import get_document
from app.services.evidence import _node_to_response
from app.services.graph import _edge_to_response, build_document_graph
from app.services.retrieval import search_evidence

DEFAULT_EXPANSION_EDGE_TYPES = {"contains", "next", "part_of", "caption_of", "near"}
MAX_EXPANSION_DEPTH = 2
MAX_EDGES_PER_LAYER = 12


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _edge_types(value: str | None) -> set[str]:
    if not value:
        return set(DEFAULT_EXPANSION_EDGE_TYPES)
    requested = {item.strip() for item in value.split(",") if item.strip()}
    return requested & DEFAULT_EXPANSION_EDGE_TYPES


def _edge_reason(edge_type: str) -> str:
    return {
        "contains": "contains_context",
        "next": "reading_order_context",
        "part_of": "table_structure_context",
        "caption_of": "caption_context",
        "near": "layout_near_context",
    }.get(edge_type, "graph_context")


def _node_query(db: Session, document_id: str, node_ids: list[str]) -> list[EvidenceNode]:
    if not node_ids:
        return []
    return (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(EvidenceNode.document_id == document_id, EvidenceNode.id.in_(node_ids))
        .all()
    )


def _candidate_response(candidate: dict) -> dict:
    return {
        "rank": candidate["rank"],
        "score": candidate["score"],
        "matched_terms": candidate["matched_terms"],
        "snippet": candidate["snippet"],
        "node": candidate["node"],
        "retrieval_source": candidate.get("retrieval_source", "hybrid"),
        "candidate_sources": candidate.get("candidate_sources", []),
        "score_breakdown": candidate.get("score_breakdown", {}),
    }


def _edge_sort_key(edge: EvidenceEdge) -> tuple[int, str]:
    type_priority = {
        "caption_of": 0,
        "part_of": 1,
        "contains": 2,
        "next": 3,
        "near": 4,
    }
    return (type_priority.get(edge.edge_type, 99), edge.id)


def _candidate_edges(
    db: Session,
    *,
    document_id: str,
    node_id: str,
    edge_types: set[str],
) -> list[EvidenceEdge]:
    edges = (
        db.query(EvidenceEdge)
        .filter(
            EvidenceEdge.document_id == document_id,
            EvidenceEdge.edge_type.in_(sorted(edge_types)),
            or_(EvidenceEdge.source_node_id == node_id, EvidenceEdge.target_node_id == node_id),
        )
        .all()
    )
    directed_edges = []
    for edge in edges:
        if edge.edge_type == "near" and edge.source_node_id != node_id:
            continue
        directed_edges.append(edge)
    return sorted(directed_edges, key=_edge_sort_key)[:MAX_EDGES_PER_LAYER]


def _other_node_id(edge: EvidenceEdge, node_id: str) -> str | None:
    if edge.source_node_id == node_id:
        return edge.target_node_id
    if edge.target_node_id == node_id:
        return edge.source_node_id
    return None


def _expand_from_candidate(
    db: Session,
    *,
    document_id: str,
    source_candidate: dict,
    max_depth: int,
    edge_types: set[str],
) -> tuple[dict[str, dict], dict[str, EvidenceEdge], set[str]]:
    source_node_id = source_candidate["node"]["id"]
    items: dict[str, dict] = {
        source_node_id: {
            "source_candidate_node_id": source_node_id,
            "source_candidate_rank": source_candidate["rank"],
            "graph_distance": 0,
            "inclusion_reason": "source_candidate",
            "path": [],
            "score_breakdown": source_candidate.get("score_breakdown", {}),
            "metadata": {
                "snippet": source_candidate["snippet"],
                "matched_terms": source_candidate["matched_terms"],
            },
        }
    }
    edges_by_id: dict[str, EvidenceEdge] = {}
    visited = {source_node_id}
    queue = deque([(source_node_id, 0, [])])

    while queue:
        current_node_id, distance, path = queue.popleft()
        if distance >= max_depth:
            continue
        for edge in _candidate_edges(
            db,
            document_id=document_id,
            node_id=current_node_id,
            edge_types=edge_types,
        ):
            next_node_id = _other_node_id(edge, current_node_id)
            if next_node_id is None or next_node_id in visited:
                continue
            visited.add(next_node_id)
            edges_by_id[edge.id] = edge
            next_path = [*path, edge]
            next_distance = distance + 1
            items[next_node_id] = {
                "source_candidate_node_id": source_node_id,
                "source_candidate_rank": source_candidate["rank"],
                "graph_distance": next_distance,
                "inclusion_reason": _edge_reason(edge.edge_type),
                "path": [_edge_to_response(path_edge) for path_edge in next_path],
                "score_breakdown": source_candidate.get("score_breakdown", {}),
                "metadata": {
                    "via_edge_type": edge.edge_type,
                    "source_candidate_score": source_candidate["score"],
                },
            }
            queue.append((next_node_id, next_distance, next_path))

    return items, edges_by_id, visited


def _merge_items(item_groups: list[dict[str, dict]]) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for group in item_groups:
        for node_id, item in group.items():
            existing = merged.get(node_id)
            if existing is None:
                merged[node_id] = item
                continue
            current_key = (item["graph_distance"], item["source_candidate_rank"])
            existing_key = (existing["graph_distance"], existing["source_candidate_rank"])
            if current_key < existing_key:
                merged[node_id] = item
    return merged


def build_evidence_pack(
    db: Session,
    document_id: str,
    query: str,
    top_k: int = 3,
    depth: int = 1,
    node_types: str | None = None,
    edge_types: str | None = None,
) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    build_document_graph(db, document_id)
    max_depth = max(0, min(depth, MAX_EXPANSION_DEPTH))
    requested_edge_types = _edge_types(edge_types)
    input_payload = {
        "query": query,
        "top_k": top_k,
        "depth": max_depth,
        "node_types": node_types,
        "edge_types": sorted(requested_edge_types),
    }
    search_payload = search_evidence(
        db,
        document_id,
        query=query,
        top_k=top_k,
        node_types=node_types,
    )
    source_candidates = [_candidate_response(candidate) for candidate in search_payload["results"]]
    item_groups: list[dict[str, dict]] = []
    edges_by_id: dict[str, EvidenceEdge] = {}
    node_ids: set[str] = set()
    for candidate in source_candidates:
        items, candidate_edges, candidate_node_ids = _expand_from_candidate(
            db,
            document_id=document_id,
            source_candidate=candidate,
            max_depth=max_depth,
            edge_types=requested_edge_types,
        )
        item_groups.append(items)
        edges_by_id.update(candidate_edges)
        node_ids.update(candidate_node_ids)

    merged_items = _merge_items(item_groups)
    ordered_node_ids = list(merged_items.keys())
    nodes = _node_query(db, document_id, ordered_node_ids)
    node_by_id = {node.id: node for node in nodes}
    items = [
        {
            "node": _node_to_response(node_by_id[node_id]),
            **item,
        }
        for node_id, item in sorted(
            merged_items.items(),
            key=lambda pair: (
                pair[1]["graph_distance"],
                pair[1]["source_candidate_rank"],
                node_by_id[pair[0]].page.page_number if pair[0] in node_by_id else 0,
                node_by_id[pair[0]].reading_order if pair[0] in node_by_id else 0,
            ),
        )
        if node_id in node_by_id
    ]
    ordered_nodes = [item["node"] for item in items]
    edge_responses = [_edge_to_response(edge) for edge in sorted(edges_by_id.values(), key=_edge_sort_key)]
    node_type_counts = Counter(item["node"]["node_type"] for item in items)
    edge_type_counts = Counter(edge["edge_type"] for edge in edge_responses)
    max_graph_distance = max((item["graph_distance"] for item in items), default=0)
    summary = {
        "source_candidate_count": len(source_candidates),
        "expanded_node_count": len(ordered_nodes),
        "edge_count": len(edge_responses),
        "item_count": len(items),
        "max_graph_distance": max_graph_distance,
        "edge_type_counts": dict(edge_type_counts),
        "node_type_counts": dict(node_type_counts),
    }
    return {
        "query": query,
        "document_id": document_id,
        "source_candidates": source_candidates,
        "nodes": ordered_nodes,
        "edges": edge_responses,
        "items": items,
        "summary": summary,
        "tool_trace": _trace(
            "build_evidence_pack",
            input_payload,
            f"{len(items)} items from {len(source_candidates)} candidates",
            start,
        ),
    }
