from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "question",
    "question_type",
    "expected_answer_terms",
    "expected_node_types",
    "expected_failure_mode",
}


def validate_curated_case(row: dict[str, Any], line_number: int | None = None) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in row)
    if missing:
        prefix = f"line {line_number}: " if line_number is not None else ""
        raise ValueError(f"{prefix}missing required curated benchmark fields: {', '.join(missing)}")
    if not isinstance(row["expected_answer_terms"], list):
        raise ValueError("expected_answer_terms must be a list")
    if not isinstance(row["expected_node_types"], list):
        raise ValueError("expected_node_types must be a list")
    return {
        **row,
        "id": str(row["id"]),
        "question": str(row["question"]),
        "question_type": str(row["question_type"]),
        "expected_answer_terms": [str(term) for term in row["expected_answer_terms"]],
        "expected_node_types": [str(node_type) for node_type in row["expected_node_types"]],
        "expected_failure_mode": str(row["expected_failure_mode"]),
        "repair_expectation": str(row.get("repair_expectation") or ""),
        "tags": [str(tag) for tag in row.get("tags", [])],
        "source_profile": str(row.get("source_profile") or "synthetic_financial_report"),
    }


def load_curated_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            cases.append(validate_curated_case(json.loads(line), line_number=index))
    return cases


def case_failure_targets(cases: list[dict[str, Any]]) -> dict[str, int]:
    targets: dict[str, int] = {}
    for case in cases:
        reason = str(case.get("expected_failure_mode") or "unknown")
        targets[reason] = targets.get(reason, 0) + 1
    return dict(sorted(targets.items()))

