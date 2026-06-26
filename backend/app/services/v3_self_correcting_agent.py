import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.claim_verification import verify_claims
from app.services.documents import get_document
from app.services.evidence_pack import build_evidence_pack
from app.services.retrieval import verify_answer_tool
from app.services.trace_store import complete_trace_run, create_trace_run, fail_trace_run, record_tool_call
from app.services.v3_failure_taxonomy import diagnose_failure
from app.services.v3_repair_policy import build_repair_plan
from app.services.v3_sufficiency import score_evidence


TABLE_KEYWORDS = {
    "revenue",
    "income",
    "margin",
    "metric",
    "table",
    "2024",
    "2025",
    "2026",
    "费用",
    "收入",
    "利润",
    "毛利",
    "表格",
    "指标",
}
STOPWORDS = {
    "what",
    "which",
    "was",
    "were",
    "the",
    "a",
    "an",
    "in",
    "on",
    "of",
    "for",
    "to",
    "and",
    "or",
    "is",
    "are",
}


def _classify_question(question: str) -> str:
    normalized = question.lower()
    if any(keyword in normalized for keyword in TABLE_KEYWORDS):
        return "table_lookup"
    if re.search(r"\d", normalized):
        return "table_lookup"
    return "text_lookup"


def _expected_terms(question: str) -> list[str]:
    terms = []
    for token in re.findall(r"[A-Za-z0-9_]+", question.lower()):
        if token in STOPWORDS or len(token) < 3:
            continue
        terms.append(token)
    return list(dict.fromkeys(terms))


def _case_from_question(question: str, question_type: str) -> dict[str, Any]:
    expected_node_types = (
        ["table", "metric_value"]
        if question_type == "table_lookup"
        else ["text_block", "ocr_text_block", "visual_summary"]
    )
    return {
        "id": "online_question",
        "question": question,
        "question_type": question_type,
        "expected_answer_terms": _expected_terms(question),
        "expected_node_types": expected_node_types,
    }


def _citation_from_item(item: dict[str, Any]) -> dict[str, Any]:
    node = item["node"]
    snippet = str(node.get("text") or "")[:220]
    return {
        "node_id": node["id"],
        "node_type": node["node_type"],
        "page_number": node["page_number"],
        "bbox": node["bbox"],
        "snippet": snippet,
    }


def _preferred_item(items: list[dict[str, Any]], expected_node_types: list[str]) -> dict[str, Any] | None:
    expected = set(expected_node_types)
    for item in items:
        if item["node"]["node_type"] in expected:
            return item
    return items[0] if items else None


def _term_hit(answer: str, terms: list[str]) -> float:
    if not terms:
        return 1.0 if answer.strip() else 0.0
    lower = answer.lower()
    hits = sum(1 for term in terms if str(term).lower() in lower)
    return hits / len(terms)


def _citation_type_hit(citations: list[dict[str, Any]], expected_node_types: list[str]) -> float:
    expected = set(expected_node_types)
    if not expected:
        return 1.0 if citations else 0.0
    citation_types = {str(citation.get("node_type")) for citation in citations}
    return 1.0 if citation_types & expected else 0.0


def _append_tool_trace(
    db: Session,
    *,
    trace_run_id: str,
    document_id: str,
    trace: list[dict[str, Any]],
    payload: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    tool_trace = payload.get("tool_trace")
    if not isinstance(tool_trace, dict):
        return
    trace.append(tool_trace)
    record_tool_call(
        db,
        trace_run_id=trace_run_id,
        document_id=document_id,
        step_index=len(trace),
        tool_trace=tool_trace,
        metadata=metadata,
    )


def _draft_answer(pack: dict[str, Any], case: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    item = _preferred_item(pack["items"], case.get("expected_node_types", []))
    if item is None:
        return "I could not find enough supporting evidence in the document.", []
    node = item["node"]
    answer = (
        f"Based on {node['node_type']} evidence on page {node['page_number']}, "
        f"{node['text']}"
    )
    return answer, [_citation_from_item(item)]


def _attempt_result(
    *,
    case: dict[str, Any],
    answer: str,
    citations: list[dict[str, Any]],
    claim_verification: dict[str, Any],
    pack: dict[str, Any],
) -> dict[str, Any]:
    summary = pack.get("summary", {})
    item_count = int(summary.get("item_count") or 0)
    source_count = int(summary.get("source_candidate_count") or 0)
    claim_status = claim_verification.get("status")
    return {
        "case_id": case["id"],
        "strategy": "v3_self_correcting_agent",
        "answer_term_hit": _term_hit(answer, case.get("expected_answer_terms", [])),
        "citation_node_type_hit": _citation_type_hit(citations, case.get("expected_node_types", [])),
        "claim_supported": 1.0 if claim_status in {"supported", "partial"} else 0.0,
        "evidence_pack_context_hit": 1.0 if item_count > source_count else 0.0,
    }


def _run_attempt(
    db: Session,
    *,
    document_id: str,
    question: str,
    case: dict[str, Any],
    trace_run_id: str,
    trace: list[dict[str, Any]],
    round_index: int,
    node_types: str | None,
    top_k: int,
    depth: int,
    query: str | None = None,
    repair_action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pack = build_evidence_pack(
        db,
        document_id,
        query=query or question,
        top_k=top_k,
        depth=depth,
        node_types=node_types,
    )
    _append_tool_trace(
        db,
        trace_run_id=trace_run_id,
        document_id=document_id,
        trace=trace,
        payload=pack,
        metadata={"round_index": round_index, "repair_action": repair_action},
    )
    answer, citations = _draft_answer(pack, case)
    verification = verify_answer_tool(
        db,
        document_id,
        answer=answer,
        citation_node_ids=[citation["node_id"] for citation in citations],
    )
    _append_tool_trace(
        db,
        trace_run_id=trace_run_id,
        document_id=document_id,
        trace=trace,
        payload=verification,
        metadata={"round_index": round_index, "repair_action": repair_action},
    )
    claim_verification = verify_claims(
        db,
        document_id,
        answer=answer,
        citations=citations,
        question_type=case["question_type"],
    )
    _append_tool_trace(
        db,
        trace_run_id=trace_run_id,
        document_id=document_id,
        trace=trace,
        payload=claim_verification,
        metadata={"round_index": round_index, "repair_action": repair_action},
    )
    result = _attempt_result(
        case=case,
        answer=answer,
        citations=citations,
        claim_verification=claim_verification,
        pack=pack,
    )
    sufficiency = score_evidence(case, result)
    diagnosis = diagnose_failure(case, result)
    return {
        "answer": answer,
        "citations": citations,
        "verification": verification,
        "claim_verification": claim_verification,
        "evidence_pack_summary": pack["summary"],
        "result_signals": result,
        "sufficiency": sufficiency,
        "diagnosis": diagnosis,
    }


def _initial_node_types(question_type: str) -> str:
    if question_type == "table_lookup":
        return "text_block"
    return "text_block"


def _query_for_action(question: str, action: dict[str, Any]) -> str:
    if action.get("action") != "query_rewrite":
        return question
    return f"{question} table metric revenue evidence"


def _node_types_for_action(case: dict[str, Any], action: dict[str, Any]) -> str | None:
    action_name = action.get("action")
    if action_name in {"node_type_expansion", "graph_depth_expansion"}:
        return None
    if action_name in {"citation_rerank", "required_type_filter"}:
        return ",".join(case.get("expected_node_types", []))
    if action_name == "vision_grounding_retry":
        return "figure,chart,visual_summary"
    return None


def _depth_for_action(action: dict[str, Any]) -> int:
    if action.get("action") == "graph_depth_expansion":
        return 2
    return int((action.get("arguments") or {}).get("depth") or 1)


def answer_self_correcting_question(
    db: Session,
    document_id: str,
    question: str,
    *,
    max_repair_rounds: int = 2,
) -> dict[str, Any]:
    clean_question = question.strip()
    if not clean_question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    get_document(db, document_id)
    question_type = _classify_question(clean_question)
    case = _case_from_question(clean_question, question_type)
    trace_run = create_trace_run(
        db,
        document_id=document_id,
        question=clean_question,
        question_type=question_type,
        metadata={"agent": "v3_self_correcting", "max_repair_rounds": max_repair_rounds},
    )
    trace: list[dict[str, Any]] = []
    repair_rounds: list[dict[str, Any]] = []
    stop_reason = "sufficient_initial"

    try:
        current = _run_attempt(
            db,
            document_id=document_id,
            question=clean_question,
            case=case,
            trace_run_id=trace_run.id,
            trace=trace,
            round_index=0,
            node_types=_initial_node_types(question_type),
            top_k=3,
            depth=0,
        )
        initial_sufficiency = current["sufficiency"]

        if current["sufficiency"]["label"] != "sufficient":
            stop_reason = "max_repair_rounds_reached"
            max_rounds = max(0, min(max_repair_rounds, 3))
            for round_index in range(1, max_rounds + 1):
                repair_plan = build_repair_plan([current["diagnosis"]], max_actions_per_diagnosis=2)
                if not repair_plan["has_repair"]:
                    stop_reason = "no_repair_action"
                    break
                action = repair_plan["actions"][0]
                repaired = _run_attempt(
                    db,
                    document_id=document_id,
                    question=clean_question,
                    case=case,
                    trace_run_id=trace_run.id,
                    trace=trace,
                    round_index=round_index,
                    node_types=_node_types_for_action(case, action),
                    top_k=5,
                    depth=_depth_for_action(action),
                    query=_query_for_action(clean_question, action),
                    repair_action=action,
                )
                repair_rounds.append(
                    {
                        "round_index": round_index,
                        "diagnosis": current["diagnosis"],
                        "repair_plan": repair_plan,
                        "selected_action": action,
                        "before_sufficiency": current["sufficiency"],
                        "after_sufficiency": repaired["sufficiency"],
                    }
                )
                if repaired["sufficiency"]["score"] >= current["sufficiency"]["score"]:
                    current = repaired
                if current["sufficiency"]["label"] == "sufficient":
                    stop_reason = "sufficient_after_repair"
                    break

        complete_trace_run(
            db,
            trace_run.id,
            answer=current["answer"],
            metadata={
                "agent": "v3_self_correcting",
                "stop_reason": stop_reason,
                "repair_round_count": len(repair_rounds),
                "initial_sufficiency": initial_sufficiency,
                "final_sufficiency": current["sufficiency"],
            },
        )
        return {
            "trace_id": trace_run.id,
            "document_id": document_id,
            "question": clean_question,
            "question_type": question_type,
            "answer": current["answer"],
            "citations": current["citations"],
            "trace": trace,
            "verification": current["verification"],
            "claim_verification": current["claim_verification"],
            "initial_sufficiency": initial_sufficiency,
            "final_sufficiency": current["sufficiency"],
            "final_diagnosis": current["diagnosis"],
            "repair_round_count": len(repair_rounds),
            "repair_rounds": repair_rounds,
            "stop_reason": stop_reason,
        }
    except Exception as exc:
        fail_trace_run(db, trace_run.id, error=str(exc))
        raise
