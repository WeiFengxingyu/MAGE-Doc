from collections import Counter
from typing import Any


REPAIR_CANDIDATES: dict[str, list[str]] = {
    "retrieval_miss": ["query_rewrite", "node_type_expansion"],
    "graph_miss": ["graph_depth_expansion", "edge_type_expansion"],
    "citation_mismatch": ["citation_rerank", "required_type_filter"],
    "unsupported_claim": ["conservative_answer_rewrite", "evidence_pack_retry"],
    "ocr_low_confidence": ["ocr_retry", "human_review_flag"],
    "visual_grounding_missing": ["vision_grounding_retry", "visual_node_search"],
    "passed": [],
}

SEVERITY_BY_REASON = {
    "retrieval_miss": "high",
    "graph_miss": "medium",
    "citation_mismatch": "medium",
    "unsupported_claim": "high",
    "ocr_low_confidence": "medium",
    "visual_grounding_missing": "medium",
    "passed": "none",
}


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _expected_node_types(case: dict[str, Any]) -> set[str]:
    node_types = {str(node_type) for node_type in case.get("expected_node_types", [])}
    for evidence in case.get("expected_evidence", []):
        if isinstance(evidence, dict) and evidence.get("node_type"):
            node_types.add(str(evidence["node_type"]))
    return node_types


def _expects_visual(case: dict[str, Any]) -> bool:
    return bool(_expected_node_types(case) & {"figure", "chart", "visual_summary"})


def _expects_ocr(case: dict[str, Any]) -> bool:
    return "ocr_text_block" in _expected_node_types(case) or bool(case.get("requires_ocr"))


def _diagnosis(
    *,
    case: dict[str, Any],
    result: dict[str, Any],
    reason: str,
    confidence: float,
    message: str,
) -> dict[str, Any]:
    signals = {
        "answer_term_hit": _score(result.get("answer_term_hit")),
        "citation_node_type_hit": _score(result.get("citation_node_type_hit")),
        "claim_supported": _score(result.get("claim_supported")),
        "evidence_pack_context_hit": _score(result.get("evidence_pack_context_hit")),
    }
    if result.get("ocr_average_confidence") is not None:
        signals["ocr_average_confidence"] = _score(result.get("ocr_average_confidence"))
    return {
        "case_id": str(result.get("case_id") or case.get("id") or case.get("qid") or ""),
        "strategy": str(result.get("strategy") or ""),
        "reason": reason,
        "severity": SEVERITY_BY_REASON[reason],
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "message": message,
        "signals": signals,
        "repair_candidates": REPAIR_CANDIDATES[reason],
    }


def diagnose_failure(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    answer_hit = _score(result.get("answer_term_hit"))
    citation_hit = _score(result.get("citation_node_type_hit"))
    claim_supported = _score(result.get("claim_supported"))
    context_hit = _score(result.get("evidence_pack_context_hit"))
    ocr_confidence = result.get("ocr_average_confidence")

    if answer_hit <= 0 and citation_hit <= 0:
        return _diagnosis(
            case=case,
            result=result,
            reason="retrieval_miss",
            confidence=0.95,
            message="No answer terms or expected evidence node types were recovered.",
        )
    if context_hit <= 0 and result.get("strategy") in {"v1_evidence_pack", "v2_multimodal_graph"}:
        return _diagnosis(
            case=case,
            result=result,
            reason="graph_miss",
            confidence=0.82,
            message="Retrieval found candidates, but graph expansion added no useful context.",
        )
    if answer_hit > 0 and citation_hit <= 0:
        return _diagnosis(
            case=case,
            result=result,
            reason="citation_mismatch",
            confidence=0.86,
            message="Answer terms were present, but citations did not match expected evidence types.",
        )
    if claim_supported <= 0:
        return _diagnosis(
            case=case,
            result=result,
            reason="unsupported_claim",
            confidence=0.9,
            message="Claim verification did not find enough support in cited evidence.",
        )
    if _expects_ocr(case) and isinstance(ocr_confidence, int | float) and float(ocr_confidence) < 0.5:
        return _diagnosis(
            case=case,
            result=result,
            reason="ocr_low_confidence",
            confidence=0.78,
            message="OCR-dependent case used low-confidence OCR evidence.",
        )
    if _expects_visual(case) and citation_hit <= 0:
        return _diagnosis(
            case=case,
            result=result,
            reason="visual_grounding_missing",
            confidence=0.78,
            message="Visual evidence was expected but not grounded in retrieved citations.",
        )
    return _diagnosis(
        case=case,
        result=result,
        reason="passed",
        confidence=1.0,
        message="All tracked reliability signals passed.",
    )


def _case_by_id(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(case.get("id") or case.get("qid")): case for case in cases}


def diagnosis_distribution(diagnoses: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(diagnosis["reason"] for diagnosis in diagnoses).items()))


def diagnose_failures(cases: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    cases_by_id = _case_by_id(cases)
    diagnoses = [
        diagnose_failure(cases_by_id.get(str(result.get("case_id")), {}), result)
        for result in results
    ]
    distribution = diagnosis_distribution(diagnoses)
    failed_count = sum(1 for diagnosis in diagnoses if diagnosis["reason"] != "passed")
    return {
        "case_count": len(cases),
        "result_count": len(results),
        "distribution": distribution,
        "failed_count": failed_count,
        "passed_count": len(diagnoses) - failed_count,
        "diagnoses": diagnoses,
    }

