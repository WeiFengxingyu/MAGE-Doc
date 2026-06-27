from datetime import datetime, timezone
import re
from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _table_cell(value: Any) -> str:
    return _safe_text(value, "-").replace("\n", " ").replace("|", "\\|")


def _score(value: dict[str, Any] | None) -> str:
    if not isinstance(value, dict):
        return "unknown"
    label = _safe_text(value.get("label"), "unknown")
    raw_score = value.get("score")
    try:
        return f"{label} {float(raw_score):.2f}"
    except (TypeError, ValueError):
        return label


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "trusted-answer-report"


def _citations_section(citations: list[dict[str, Any]]) -> list[str]:
    lines = ["## Citations", ""]
    if not citations:
        return lines + ["No citations were returned.", ""]

    lines.extend(
        [
            "| # | Type | Page | BBox | Snippet |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for index, citation in enumerate(citations, start=1):
        bbox = citation.get("bbox") or []
        bbox_text = ", ".join(str(item) for item in bbox) if isinstance(bbox, list) else _safe_text(bbox)
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _table_cell(citation.get("node_type")),
                    _table_cell(citation.get("page_number")),
                    _table_cell(bbox_text),
                    _table_cell(citation.get("snippet")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _repair_rounds_section(rounds: list[dict[str, Any]]) -> list[str]:
    lines = ["## Repair Rounds", ""]
    if not rounds:
        return lines + ["No repair round was required.", ""]

    lines.extend(
        [
            "| Round | Diagnosis | Action | Before | After |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for round_item in rounds:
        diagnosis = round_item.get("diagnosis") or {}
        action = round_item.get("selected_action") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(round_item.get("round_index")),
                    _table_cell(diagnosis.get("reason")),
                    _table_cell(action.get("action")),
                    _table_cell(_score(round_item.get("before_sufficiency"))),
                    _table_cell(_score(round_item.get("after_sufficiency"))),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _claim_section(claim_verification: dict[str, Any] | None) -> list[str]:
    lines = ["## Claim Verification", ""]
    if not isinstance(claim_verification, dict):
        return lines + ["No claim verification payload was returned.", ""]

    lines.extend(
        [
            f"- Status: {_safe_text(claim_verification.get('status'), 'unknown')}",
            f"- Claims: {_safe_text(claim_verification.get('claim_count'), '0')}",
            f"- Supported: {_safe_text(claim_verification.get('supported_count'), '0')}",
            f"- Partial: {_safe_text(claim_verification.get('partial_count'), '0')}",
            f"- Unsupported: {_safe_text(claim_verification.get('unsupported_count'), '0')}",
            "",
        ]
    )

    claims = claim_verification.get("claims") or []
    if not claims:
        return lines

    lines.extend(
        [
            "| Claim | Status | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for claim in claims:
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(claim.get("claim")),
                    _table_cell(claim.get("status")),
                    _table_cell(claim.get("reason")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _trace_section(trace: list[dict[str, Any]]) -> list[str]:
    lines = ["## Tool Trace", ""]
    if not trace:
        return lines + ["No tool trace was returned.", ""]

    lines.extend(
        [
            "| Step | Tool | Latency | Output |",
            "| --- | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(trace, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _table_cell(item.get("tool_name")),
                    _table_cell(f"{item.get('latency_ms', 0)} ms"),
                    _table_cell(item.get("output_summary")),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def generate_trusted_answer_report(
    *,
    title: str,
    question: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    clean_title = _safe_text(title, "Trusted Answer Report")
    clean_question = _safe_text(question or response.get("question"), "Untitled question")
    final_sufficiency = response.get("final_sufficiency") or {}
    initial_sufficiency = response.get("initial_sufficiency") or {}
    diagnosis = response.get("final_diagnosis") or {}
    citations = response.get("citations") or []
    repair_rounds = response.get("repair_rounds") or []
    trace = response.get("trace") or []
    claim_verification = response.get("claim_verification")

    try:
        final_score = float(final_sufficiency.get("score") or 0)
    except (TypeError, ValueError):
        final_score = 0.0

    summary = {
        "final_sufficiency": _safe_text(final_sufficiency.get("label"), "unknown"),
        "final_sufficiency_score": round(final_score, 4),
        "repair_round_count": int(response.get("repair_round_count") or len(repair_rounds)),
        "citation_count": len(citations),
        "diagnosis_reason": _safe_text(diagnosis.get("reason"), "unknown"),
    }

    lines = [
        f"# {clean_title}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Question | {_table_cell(clean_question)} |",
        f"| Trace ID | {_table_cell(response.get('trace_id'))} |",
        f"| Stop Reason | {_table_cell(response.get('stop_reason'))} |",
        f"| Initial Sufficiency | {_table_cell(_score(initial_sufficiency))} |",
        f"| Final Sufficiency | {_table_cell(_score(final_sufficiency))} |",
        f"| Diagnosis | {_table_cell(diagnosis.get('reason'))} |",
        "",
        "## Answer",
        "",
        _safe_text(response.get("answer"), "No answer was returned."),
        "",
        "## Final Diagnosis",
        "",
        f"- Reason: {_safe_text(diagnosis.get('reason'), 'unknown')}",
        f"- Severity: {_safe_text(diagnosis.get('severity'), 'unknown')}",
        f"- Confidence: {_safe_text(diagnosis.get('confidence'), 'unknown')}",
        f"- Message: {_safe_text(diagnosis.get('message'), 'No diagnostic message.')}",
        "",
    ]
    lines.extend(_citations_section(citations))
    lines.extend(_repair_rounds_section(repair_rounds))
    lines.extend(_claim_section(claim_verification))
    lines.extend(_trace_section(trace))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{_slugify(clean_title)}-{timestamp}.md"
    return {
        "filename": filename,
        "markdown": "\n".join(lines).strip() + "\n",
        "summary": summary,
    }
