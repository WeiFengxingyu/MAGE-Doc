import json
import math
import re
import time
from collections import Counter
from hashlib import blake2b
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.evidence import EvidenceNode
from app.models.page import Page
from app.services.documents import get_document
from app.services.evidence import TABLE_NODE_TYPE, _json_loads, _node_to_response
from app.services.pages import get_page

DEFAULT_NODE_TYPES = {"text_block", "table"}
ASCII_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
TABLE_QUERY_TERMS = {"table", "metric", "revenue", "income", "margin", "表", "指标", "收入", "利润"}
SUMMARY_QUERY_TERMS = {"summary", "reason", "risk", "概括", "总结", "原因", "风险"}


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _tokenize(value: str) -> list[str]:
    normalized = value.lower()
    tokens = ASCII_TOKEN_PATTERN.findall(normalized)
    cjk_chars = CJK_PATTERN.findall(normalized)
    tokens.extend(cjk_chars)
    tokens.extend(
        "".join(pair)
        for pair in zip(cjk_chars, cjk_chars[1:], strict=False)
        if pair[0].strip() and pair[1].strip()
    )
    return tokens


def _metadata_text(metadata: dict[str, Any]) -> str:
    parts: list[str] = []
    matrix = metadata.get("matrix")
    if isinstance(matrix, list):
        for row in matrix:
            if isinstance(row, list):
                parts.extend(str(cell or "") for cell in row)
    for key in ("row_count", "col_count", "source", "method"):
        if key in metadata:
            parts.append(str(metadata[key]))
    return " ".join(parts)


def _searchable_text(node: EvidenceNode) -> str:
    metadata = _json_loads(node.metadata_json, {})
    return f"{node.text} {_metadata_text(metadata)}"


def _stable_bucket(token: str, dimensions: int = 64) -> int:
    digest = blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") % dimensions


def _hashed_vector(tokens: list[str], dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in tokens:
        vector[_stable_bucket(token, dimensions)] += 1.0
    return vector


def _cosine(first: list[float], second: list[float]) -> float:
    numerator = sum(left * right for left, right in zip(first, second, strict=True))
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0 or second_norm == 0:
        return 0.0
    return numerator / (first_norm * second_norm)


def _semantic_score(query_terms: list[str], document_terms: list[str]) -> float:
    if not query_terms or not document_terms:
        return 0.0
    return _cosine(_hashed_vector(query_terms), _hashed_vector(document_terms))


def _metadata_score(query_terms: list[str], node: EvidenceNode) -> float:
    metadata = _json_loads(node.metadata_json, {})
    query_set = set(query_terms)
    score = 0.0
    if query_set & TABLE_QUERY_TERMS and node.node_type in {"table", "table_cell"}:
        score += 0.6
    if any(term.isdigit() for term in query_terms) and node.node_type in {"table", "table_cell"}:
        score += 0.25
    if query_set & SUMMARY_QUERY_TERMS and node.node_type in {"text_block", "section", "caption"}:
        score += 0.25
    if metadata.get("is_header") is True:
        score += 0.15
    if node.node_type == "caption" and query_set & TABLE_QUERY_TERMS:
        score += 0.2
    return min(score, 1.0)


def _snippet(value: str, matched_terms: list[str], max_length: int = 180) -> str:
    clean = " ".join(value.split())
    if len(clean) <= max_length:
        return clean
    lower = clean.lower()
    positions = [lower.find(term.lower()) for term in matched_terms if lower.find(term.lower()) >= 0]
    start = max(0, min(positions) - 40) if positions else 0
    end = min(len(clean), start + max_length)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(clean) else ""
    return f"{prefix}{clean[start:end]}{suffix}"


def _node_types(value: str | None) -> set[str]:
    if not value:
        return set(DEFAULT_NODE_TYPES)
    requested = {item.strip() for item in value.split(",") if item.strip()}
    return requested & DEFAULT_NODE_TYPES


def _query_nodes(db: Session, document_id: str, node_types: set[str]) -> list[EvidenceNode]:
    if not node_types:
        return []
    return (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.node_type.in_(sorted(node_types)),
        )
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )


def search_evidence(
    db: Session,
    document_id: str,
    query: str,
    top_k: int = 5,
    node_types: str | None = None,
) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    clean_query = query.strip()
    requested_types = _node_types(node_types)
    input_payload = {
        "query": query,
        "top_k": top_k,
        "node_types": sorted(requested_types),
    }
    if not clean_query:
        return {
            "query": query,
            "document_id": document_id,
            "results": [],
            "tool_trace": _trace("search_evidence", input_payload, "empty query", start),
        }

    nodes = _query_nodes(db, document_id, requested_types)
    query_terms = _tokenize(clean_query)
    if not query_terms or not nodes:
        return {
            "query": query,
            "document_id": document_id,
            "results": [],
            "tool_trace": _trace("search_evidence", input_payload, "0 results", start),
        }

    searchable_texts = [_searchable_text(node) for node in nodes]
    documents = [_tokenize(searchable_text) for searchable_text in searchable_texts]
    doc_freq: Counter[str] = Counter()
    for tokens in documents:
        doc_freq.update(set(tokens))

    avg_len = sum(len(tokens) for tokens in documents) / max(len(documents), 1)
    k1 = 1.5
    b = 0.75
    lexical_scores: dict[str, float] = {}
    matched_by_node: dict[str, list[str]] = {}
    unique_query_terms = list(dict.fromkeys(query_terms))
    for node, tokens in zip(nodes, documents, strict=True):
        term_counts = Counter(tokens)
        score = 0.0
        matched_terms: list[str] = []
        for term in unique_query_terms:
            tf = term_counts.get(term, 0)
            if tf == 0:
                continue
            matched_terms.append(term)
            df = doc_freq[term]
            idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            denominator = tf + k1 * (1 - b + b * (len(tokens) / max(avg_len, 1)))
            score += idf * ((tf * (k1 + 1)) / denominator)
        lexical_scores[node.id] = score
        matched_by_node[node.id] = matched_terms

    max_lexical = max(lexical_scores.values(), default=0.0)
    scored: list[tuple[float, EvidenceNode, list[str], str, dict[str, float], list[str]]] = []
    for node, tokens, searchable_text in zip(nodes, documents, searchable_texts, strict=True):
        raw_lexical = lexical_scores.get(node.id, 0.0)
        lexical_score = raw_lexical / max_lexical if max_lexical > 0 else 0.0
        semantic_score = _semantic_score(query_terms, tokens)
        metadata_score = _metadata_score(query_terms, node)
        hybrid_score = (lexical_score * 0.65) + (semantic_score * 0.25) + (metadata_score * 0.10)
        if hybrid_score <= 0:
            continue
        candidate_sources: list[str] = []
        if lexical_score > 0:
            candidate_sources.append("lexical")
        if semantic_score > 0:
            candidate_sources.append("semantic_fallback")
        if metadata_score > 0:
            candidate_sources.append("metadata")
        breakdown = {
            "lexical": round(lexical_score, 6),
            "semantic": round(semantic_score, 6),
            "metadata": round(metadata_score, 6),
            "hybrid": round(hybrid_score, 6),
        }
        scored.append(
            (
                hybrid_score,
                node,
                matched_by_node.get(node.id, []),
                searchable_text,
                breakdown,
                candidate_sources,
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1].page.page_number, item[1].reading_order))
    limited = scored[: max(1, min(top_k, 20))]
    results = [
        {
            "rank": index,
            "score": round(score, 6),
            "matched_terms": matched_terms,
            "snippet": _snippet(searchable_text, matched_terms),
            "node": _node_to_response(node),
            "retrieval_source": "hybrid",
            "candidate_sources": candidate_sources,
            "score_breakdown": breakdown,
        }
        for index, (score, node, matched_terms, searchable_text, breakdown, candidate_sources) in enumerate(
            limited,
            start=1,
        )
    ]
    return {
        "query": query,
        "document_id": document_id,
        "results": results,
        "tool_trace": _trace(
            "search_evidence",
            input_payload,
            f"{len(results)} hybrid candidates",
            start,
        ),
    }


def inspect_page_tool(db: Session, document_id: str, page_number: int) -> dict:
    start = time.perf_counter()
    page = get_page(db, document_id, page_number)
    nodes = (
        db.query(EvidenceNode)
        .filter(EvidenceNode.page_id == page.id)
        .order_by(EvidenceNode.reading_order.asc())
        .all()
    )
    evidence = [
        {
            "node_id": node.id,
            "node_type": node.node_type,
            "bbox": _json_loads(node.bbox_json, []),
            "reading_order": node.reading_order,
            "snippet": _snippet(node.text, [], max_length=120),
        }
        for node in nodes
    ]
    input_payload = {"page_number": page_number}
    return {
        "document_id": document_id,
        "page_id": page.id,
        "page_number": page.page_number,
        "width": page.width,
        "height": page.height,
        "image_url": f"/api/documents/{page.document_id}/pages/{page.page_number}/image",
        "evidence_count": len(evidence),
        "evidence": evidence,
        "tool_trace": _trace("inspect_page", input_payload, f"{len(evidence)} evidence nodes", start),
    }


def read_table_tool(db: Session, document_id: str, table_id: str) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    table = (
        db.query(EvidenceNode)
        .options(joinedload(EvidenceNode.page))
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.id == table_id,
            EvidenceNode.node_type == TABLE_NODE_TYPE,
        )
        .one_or_none()
    )
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table evidence node not found",
        )
    metadata = _json_loads(table.metadata_json, {})
    matrix = metadata.get("matrix") if isinstance(metadata.get("matrix"), list) else []
    cells = metadata.get("cells") if isinstance(metadata.get("cells"), list) else []
    input_payload = {"table_id": table_id}
    return {
        "document_id": document_id,
        "table_id": table.id,
        "page_number": table.page.page_number,
        "bbox": _json_loads(table.bbox_json, []),
        "row_count": int(metadata.get("row_count") or len(matrix)),
        "col_count": int(metadata.get("col_count") or max((len(row) for row in matrix), default=0)),
        "matrix": matrix,
        "cells": cells,
        "text": table.text,
        "tool_trace": _trace("read_table", input_payload, f"{len(matrix)} rows", start),
    }


def verify_answer_tool(
    db: Session,
    document_id: str,
    answer: str,
    citation_node_ids: list[str],
) -> dict:
    start = time.perf_counter()
    get_document(db, document_id)
    unique_ids = list(dict.fromkeys(citation_node_ids))
    existing = (
        db.query(EvidenceNode.id)
        .filter(
            EvidenceNode.document_id == document_id,
            EvidenceNode.id.in_(unique_ids) if unique_ids else False,
        )
        .all()
    )
    covered = [row[0] for row in existing]
    missing = [node_id for node_id in unique_ids if node_id not in set(covered)]
    answer_present = bool(answer.strip())
    passed = answer_present and bool(covered) and not missing
    input_payload = {
        "answer_length": len(answer.strip()),
        "citation_count": len(unique_ids),
    }
    return {
        "document_id": document_id,
        "passed": passed,
        "answer_present": answer_present,
        "citation_count": len(unique_ids),
        "covered_citation_node_ids": covered,
        "missing_citation_node_ids": missing,
        "tool_trace": _trace("verify_answer", input_payload, "passed" if passed else "failed", start),
    }
