from typing import Any


WEIGHTS = {
    "answer_term_hit": 0.25,
    "citation_node_type_hit": 0.20,
    "claim_supported": 0.25,
    "evidence_pack_context_hit": 0.15,
    "ocr_confidence": 0.075,
    "visual_grounding": 0.075,
}


def _score(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _expected_node_types(case: dict[str, Any]) -> set[str]:
    node_types = {str(node_type) for node_type in case.get("expected_node_types", [])}
    for evidence in case.get("expected_evidence", []):
        if isinstance(evidence, dict) and evidence.get("node_type"):
            node_types.add(str(evidence["node_type"]))
    return node_types


def _requires_ocr(case: dict[str, Any]) -> bool:
    return "ocr_text_block" in _expected_node_types(case) or bool(case.get("requires_ocr"))


def _requires_visual(case: dict[str, Any]) -> bool:
    return bool(_expected_node_types(case) & {"figure", "chart", "visual_summary"})


def _label(score: float) -> str:
    if score >= 0.75:
        return "sufficient"
    if score >= 0.45:
        return "partial"
    return "insufficient"


def _recommended_policy(missing_signals: list[str]) -> str | None:
    for signal, policy in (
        ("answer_term_hit", "query_rewrite"),
        ("citation_node_type_hit", "citation_rerank"),
        ("claim_supported", "conservative_answer_rewrite"),
        ("evidence_pack_context_hit", "graph_depth_expansion"),
        ("ocr_confidence", "ocr_retry"),
        ("visual_grounding", "vision_grounding_retry"),
    ):
        if signal in missing_signals:
            return policy
    return None


def score_evidence(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    signals = {
        "answer_term_hit": _score(result.get("answer_term_hit")),
        "citation_node_type_hit": _score(result.get("citation_node_type_hit")),
        "claim_supported": _score(result.get("claim_supported")),
        "evidence_pack_context_hit": _score(result.get("evidence_pack_context_hit")),
        "ocr_confidence": _score(result.get("ocr_average_confidence"), default=1.0),
        "visual_grounding": _score(result.get("visual_grounding"), default=1.0),
    }
    if _requires_ocr(case):
        signals["ocr_confidence"] = _score(result.get("ocr_average_confidence"))
    if _requires_visual(case):
        signals["visual_grounding"] = _score(result.get("visual_grounding"))

    raw_score = sum(signals[key] * weight for key, weight in WEIGHTS.items())
    if signals["answer_term_hit"] < 0.5 or signals["claim_supported"] < 0.5:
        raw_score = min(raw_score, 0.44)
    elif signals["citation_node_type_hit"] < 0.5:
        raw_score = min(raw_score, 0.74)
    score = round(raw_score, 4)
    missing = [key for key, value in signals.items() if value < 0.5]
    return {
        "score": score,
        "label": _label(score),
        "signals": signals,
        "missing_signals": missing,
        "recommended_policy": _recommended_policy(missing),
    }


def _term_hit(answer: str, terms: list[str]) -> float:
    if not terms:
        return 1.0 if answer.strip() else 0.0
    lower = answer.lower()
    hits = sum(1 for term in terms if str(term).lower() in lower)
    return hits / len(terms)


def score_agent_answer(question: str, answer_payload: dict[str, Any], case: dict[str, Any] | None = None) -> dict[str, Any]:
    case_payload = case or {
        "id": "online_question",
        "question": question,
        "expected_answer_terms": [],
        "expected_node_types": [],
    }
    citations = answer_payload.get("citations", [])
    claim_status = (answer_payload.get("claim_verification") or {}).get("status")
    expected_types = _expected_node_types(case_payload)
    citation_types = {str(citation.get("node_type")) for citation in citations if citation.get("node_type")}
    result = {
        "answer_term_hit": _term_hit(
            str(answer_payload.get("answer") or ""),
            [str(term) for term in case_payload.get("expected_answer_terms", [])],
        ),
        "citation_node_type_hit": 1.0
        if not expected_types or bool(citation_types & expected_types)
        else 0.0,
        "claim_supported": 1.0 if claim_status in {"supported", "partial"} else 0.0,
        "evidence_pack_context_hit": 1.0 if len(citations) > 0 else 0.0,
    }
    return score_evidence(case_payload, result)
