from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _node_types_from_expected_evidence(row: dict[str, Any]) -> list[str]:
    node_types: list[str] = []
    for evidence in row.get("expected_evidence", []):
        if isinstance(evidence, dict) and evidence.get("node_type"):
            node_types.append(str(evidence["node_type"]))
    return list(dict.fromkeys(node_types))


def benchmark_to_internal_case(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    answers = row.get("answers", [])
    if isinstance(answers, str):
        answers = [answers]
    expected_terms = row.get("expected_answer_terms", answers)
    expected_types = row.get("expected_node_types") or _node_types_from_expected_evidence(row)
    question = row.get("question") or row.get("query") or ""
    question_type = row.get("question_type") or metadata.get("question_type") or "text_lookup"
    return {
        "id": str(row.get("id") or row.get("qid") or ""),
        "question": str(question),
        "question_type": str(question_type),
        "expected_answer_terms": [str(term) for term in expected_terms],
        "expected_node_types": [str(node_type) for node_type in expected_types],
        "expected_claim_status": str(row.get("expected_claim_status") or "supported"),
        "metadata": metadata,
    }


def load_benchmark_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(benchmark_to_internal_case(json.loads(line)))
    return cases


def _submission_evidence(result: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = result.get("evidence") or result.get("citations") or []
    normalized: list[dict[str, Any]] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "document_id": str(item.get("document_id") or ""),
                "node_id": str(item.get("node_id") or item.get("id") or ""),
                "page_number": item.get("page_number"),
                "bbox": item.get("bbox", []),
            }
        )
    return normalized


def export_submission(
    results: list[dict[str, Any]],
    output: Path,
    run_name: str = "magedoc_v2_benchmark_adapter",
) -> dict[str, Any]:
    payload = {
        "run_name": run_name,
        "result_count": len(results),
        "results": [
            {
                "qid": str(result.get("qid") or result.get("case_id") or ""),
                "answer": str(result.get("answer") or result.get("generated_answer") or ""),
                "evidence": _submission_evidence(result),
            }
            for result in results
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def build_failure_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        reason = str(result.get("failure_reason") or result.get("reason") or "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return {"distribution": dict(sorted(counts.items())), "result_count": len(results)}

