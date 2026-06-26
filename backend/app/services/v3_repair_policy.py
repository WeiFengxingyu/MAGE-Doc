from typing import Any


POLICY_TABLE: dict[str, list[dict[str, Any]]] = {
    "retrieval_miss": [
        {
            "action": "query_rewrite",
            "description": "Rewrite the query with document-analysis terms.",
            "tool_plan": ["search_evidence"],
            "arguments": {"rewrite_mode": "domain_terms", "top_k": 5},
            "cost_level": "low",
            "stop_rule": "stop_if_results_found",
        },
        {
            "action": "node_type_expansion",
            "description": "Retry retrieval across all multimodal evidence node types.",
            "tool_plan": ["search_evidence", "build_evidence_pack"],
            "arguments": {"node_types": None, "top_k": 5, "depth": 1},
            "cost_level": "low",
            "stop_rule": "stop_if_score_improves",
        },
    ],
    "graph_miss": [
        {
            "action": "graph_depth_expansion",
            "description": "Increase evidence graph expansion depth.",
            "tool_plan": ["build_evidence_pack"],
            "arguments": {"depth": 2, "top_k": 5},
            "cost_level": "medium",
            "stop_rule": "stop_if_context_added",
        }
    ],
    "citation_mismatch": [
        {
            "action": "citation_rerank",
            "description": "Prefer candidates with required evidence node types.",
            "tool_plan": ["search_evidence"],
            "arguments": {"prefer_required_node_types": True, "top_k": 5},
            "cost_level": "low",
            "stop_rule": "stop_if_required_type_found",
        }
    ],
    "unsupported_claim": [
        {
            "action": "conservative_answer_rewrite",
            "description": "Rewrite answer using only verified citation text.",
            "tool_plan": ["verify_claims"],
            "arguments": {"mode": "citation_only"},
            "cost_level": "low",
            "stop_rule": "stop_after_rewrite",
        }
    ],
    "ocr_low_confidence": [
        {
            "action": "ocr_retry",
            "description": "Retry OCR or flag page for human review.",
            "tool_plan": ["run_ocr"],
            "arguments": {"min_text_chars": 5},
            "cost_level": "medium",
            "stop_rule": "stop_if_confidence_improves",
        }
    ],
    "visual_grounding_missing": [
        {
            "action": "vision_grounding_retry",
            "description": "Run vision grounding and search visual nodes.",
            "tool_plan": ["run_vision_grounding", "search_evidence"],
            "arguments": {"node_types": "figure,chart,visual_summary", "top_k": 5},
            "cost_level": "medium",
            "stop_rule": "stop_if_visual_evidence_found",
        }
    ],
    "passed": [],
}


def select_repair_actions(diagnosis: dict[str, Any], max_actions: int = 2) -> list[dict[str, Any]]:
    reason = str(diagnosis.get("reason") or "")
    actions = POLICY_TABLE.get(reason, [])[: max(0, max_actions)]
    return [
        {
            **action,
            "reason": reason,
            "diagnosis_confidence": diagnosis.get("confidence", 0.0),
        }
        for action in actions
    ]


def build_repair_plan(diagnoses: list[dict[str, Any]], max_actions_per_diagnosis: int = 2) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for diagnosis in diagnoses:
        if diagnosis.get("reason") == "passed":
            continue
        actions.extend(select_repair_actions(diagnosis, max_actions=max_actions_per_diagnosis))
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for action in actions:
        action_name = str(action.get("action"))
        if action_name in seen:
            continue
        seen.add(action_name)
        deduped.append(action)
    return {
        "action_count": len(deduped),
        "actions": deduped,
        "has_repair": bool(deduped),
    }

