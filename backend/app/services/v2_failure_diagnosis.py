from collections import Counter
from typing import Any


PASSING_REASON = "All tracked benchmark signals passed."


def _case_by_id(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(case.get("id") or case.get("qid")): case for case in cases}


def _expects_visual(case: dict[str, Any]) -> bool:
    expected_types = set(case.get("expected_node_types", []))
    for evidence in case.get("expected_evidence", []):
        node_type = evidence.get("node_type") if isinstance(evidence, dict) else None
        if node_type:
            expected_types.add(str(node_type))
    return bool(expected_types & {"figure", "chart", "visual_summary"})


def _expects_ocr(case: dict[str, Any]) -> bool:
    expected_types = set(case.get("expected_node_types", []))
    return "ocr_text_block" in expected_types or bool(case.get("requires_ocr"))


def diagnose_result(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    answer_hit = float(result.get("answer_term_hit", 0.0) or 0.0)
    citation_hit = float(result.get("citation_node_type_hit", 0.0) or 0.0)
    claim_supported = float(result.get("claim_supported", 0.0) or 0.0)
    context_hit = float(result.get("evidence_pack_context_hit", 0.0) or 0.0)
    ocr_confidence = result.get("ocr_average_confidence")

    if answer_hit <= 0 and citation_hit <= 0:
        reason = "retrieval_miss"
        message = "No expected answer terms or evidence node types were recovered."
    elif context_hit <= 0 and result.get("strategy") in {"v1_evidence_pack", "v2_multimodal_graph"}:
        reason = "graph_miss"
        message = "Source candidates were found, but graph expansion added no useful context."
    elif answer_hit > 0 and citation_hit <= 0:
        reason = "citation_mismatch"
        message = "Answer terms were present, but citations did not match expected evidence types."
    elif claim_supported <= 0:
        reason = "unsupported_claim"
        message = "Claim verification did not find enough support in cited evidence."
    elif _expects_ocr(case) and isinstance(ocr_confidence, int | float) and ocr_confidence < 0.5:
        reason = "ocr_low_confidence"
        message = "OCR-dependent case used low-confidence OCR evidence."
    elif _expects_visual(case) and citation_hit <= 0:
        reason = "visual_grounding_missing"
        message = "Visual evidence was expected but not grounded in retrieved citations."
    else:
        reason = "passed"
        message = PASSING_REASON

    return {
        "case_id": str(result.get("case_id") or case.get("id") or case.get("qid") or ""),
        "strategy": str(result.get("strategy") or ""),
        "reason": reason,
        "message": message,
        "signals": {
            "answer_term_hit": answer_hit,
            "citation_node_type_hit": citation_hit,
            "claim_supported": claim_supported,
            "evidence_pack_context_hit": context_hit,
        },
    }


def summarize_diagnoses(diagnoses: list[dict[str, Any]]) -> dict[str, Any]:
    distribution = Counter(diagnosis["reason"] for diagnosis in diagnoses)
    failing = [diagnosis for diagnosis in diagnoses if diagnosis["reason"] != "passed"]
    return {
        "distribution": dict(sorted(distribution.items())),
        "failed_count": len(failing),
        "passed_count": len(diagnoses) - len(failing),
    }


def diagnose_results(cases: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    cases_by_id = _case_by_id(cases)
    diagnoses = [
        diagnose_result(cases_by_id.get(str(result.get("case_id")), {}), result)
        for result in results
    ]
    summary = summarize_diagnoses(diagnoses)
    return {
        "case_count": len(cases),
        "result_count": len(results),
        **summary,
        "diagnoses": diagnoses,
    }

