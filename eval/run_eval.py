from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from statistics import mean
from typing import Any

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "eval"
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.v2_failure_diagnosis import diagnose_results  # noqa: E402
from app.services.v3_failure_taxonomy import diagnose_failures  # noqa: E402

DEFAULT_CASES = ROOT / "eval" / "cases" / "sample_cases.jsonl"
DEFAULT_V3_CASES = ROOT / "eval" / "cases" / "v3_curated_cases.jsonl"

import curated_benchmark  # noqa: E402


def _draw_table(page: fitz.Page, x0: float, y0: float) -> None:
    col_widths = [90, 90, 90]
    row_heights = [28, 28, 28]
    xs = [x0]
    for width in col_widths:
        xs.append(xs[-1] + width)
    ys = [y0]
    for height in row_heights:
        ys.append(ys[-1] + height)
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), color=(0, 0, 0), width=0.8)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), color=(0, 0, 0), width=0.8)
    values = [["Metric", "2025", "2026"], ["Revenue", "100", "128"], ["Margin", "18%", "22%"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def synthetic_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=420, height=320)
    first.insert_text((60, 45), "1. Financial Highlights")
    first.insert_text((60, 70), "Revenue increased because enterprise demand improved.")
    first.insert_text((60, 100), "Table 1. Revenue summary")
    _draw_table(first, 60, 125)
    second = pdf.new_page(width=420, height=320)
    second.insert_text((60, 50), "Risk factors include supply chain delays.")
    return pdf.tobytes()


def load_cases(path: Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def load_v3_cases(path: Path = DEFAULT_V3_CASES) -> list[dict[str, Any]]:
    return curated_benchmark.load_curated_cases(path)


def make_client(workdir: Path) -> tuple[TestClient, Any]:
    database_url = f"sqlite:///{workdir / 'eval.sqlite'}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), engine


def prepare_document(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/documents",
        files={"file": ("magedoc-eval.pdf", synthetic_pdf_bytes(), "application/pdf")},
    )
    response.raise_for_status()
    document = response.json()
    prepare = client.post(f"/api/documents/{document['id']}/prepare-demo")
    prepare.raise_for_status()
    return document


def prepare_v2_layers(client: TestClient, document_id: str) -> None:
    for endpoint in ("ocr", "vision-grounding", "metric-graph/build"):
        response = client.post(f"/api/documents/{document_id}/{endpoint}")
        response.raise_for_status()


def _contains_terms(value: str, terms: list[str]) -> float:
    lower = value.lower()
    if not terms:
        return 1.0
    hits = sum(1 for term in terms if term.lower() in lower)
    return hits / len(terms)


def run_v0_agent_case(client: TestClient, document_id: str, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    response = client.post(
        f"/api/documents/{document_id}/questions",
        json={"question": case["question"]},
    )
    response.raise_for_status()
    payload = response.json()
    citation_types = {citation["node_type"] for citation in payload["citations"]}
    expected_types = set(case.get("expected_node_types", []))
    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "case_id": case["id"],
        "strategy": "v0_agent_baseline",
        "answer_term_hit": _contains_terms(payload["answer"], case.get("expected_answer_terms", [])),
        "citation_node_type_hit": 1.0 if citation_types & expected_types else 0.0,
        "claim_supported": 1.0
        if payload.get("claim_verification", {}).get("status") in {"supported", "partial"}
        else 0.0,
        "tool_calls": len(payload["trace"]),
        "latency_ms": latency_ms,
    }


def run_v1_pack_case(client: TestClient, document_id: str, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    node_types = "table" if case["question_type"] == "table_lookup" else "text_block"
    response = client.get(
        f"/api/documents/{document_id}/evidence-pack",
        params={"query": case["question"], "top_k": 2, "depth": 1, "node_types": node_types},
    )
    response.raise_for_status()
    payload = response.json()
    item_text = " ".join(item["node"]["text"] for item in payload["items"])
    item_types = {item["node"]["node_type"] for item in payload["items"]}
    expected_types = set(case.get("expected_node_types", []))
    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "case_id": case["id"],
        "strategy": "v1_evidence_pack",
        "answer_term_hit": _contains_terms(item_text, case.get("expected_answer_terms", [])),
        "citation_node_type_hit": 1.0 if item_types & expected_types else 0.0,
        "claim_supported": 0.0,
        "tool_calls": 1,
        "latency_ms": latency_ms,
        "evidence_pack_context_hit": 1.0 if payload["summary"]["item_count"] > len(payload["source_candidates"]) else 0.0,
    }


def run_v2_multimodal_case(client: TestClient, document_id: str, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    response = client.get(
        f"/api/documents/{document_id}/evidence-pack",
        params={"query": case["question"], "top_k": 3, "depth": 1},
    )
    response.raise_for_status()
    payload = response.json()
    item_text = " ".join(item["node"]["text"] for item in payload["items"])
    item_types = {item["node"]["node_type"] for item in payload["items"]}
    expected_types = set(case.get("expected_node_types", []))
    answer_hit = _contains_terms(item_text, case.get("expected_answer_terms", []))
    citation_hit = 1.0 if item_types & expected_types else 0.0
    latency_ms = int((time.perf_counter() - start) * 1000)
    evidence = [
        {
            "document_id": item["node"]["document_id"],
            "node_id": item["node"]["id"],
            "page_number": item["node"]["page_number"],
            "bbox": item["node"]["bbox"],
        }
        for item in payload["items"][:3]
    ]
    return {
        "case_id": case["id"],
        "strategy": "v2_multimodal_graph",
        "answer": item_text[:500],
        "answer_term_hit": answer_hit,
        "citation_node_type_hit": citation_hit,
        "claim_supported": 1.0 if answer_hit > 0 and citation_hit > 0 else 0.0,
        "tool_calls": 4,
        "latency_ms": latency_ms,
        "evidence_pack_context_hit": 1.0
        if payload["summary"]["item_count"] > len(payload["source_candidates"])
        else 0.0,
        "evidence": evidence,
    }


def run_v3_self_correcting_case(client: TestClient, document_id: str, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    response = client.post(
        f"/api/v3/documents/{document_id}/self-correcting-questions",
        json={"question": case["question"], "max_repair_rounds": 2},
    )
    response.raise_for_status()
    payload = response.json()
    latency_ms = int((time.perf_counter() - start) * 1000)
    final = payload["final_sufficiency"]
    initial = payload["initial_sufficiency"]
    final_diagnosis = payload["final_diagnosis"]
    recovery = 1.0 if initial["label"] != "sufficient" and final["label"] in {"partial", "sufficient"} else 0.0
    repair_success = (
        1.0
        if payload["repair_round_count"] > 0 and final["score"] >= initial["score"]
        else 0.0
    )
    return {
        "case_id": case["id"],
        "strategy": "v3_self_correcting",
        "answer": payload["answer"],
        "answer_term_hit": final["signals"].get("answer_term_hit", 0.0),
        "citation_node_type_hit": final["signals"].get("citation_node_type_hit", 0.0),
        "claim_supported": final["signals"].get("claim_supported", 0.0),
        "tool_calls": len(payload["trace"]),
        "latency_ms": latency_ms,
        "evidence_pack_context_hit": final["signals"].get("evidence_pack_context_hit", 0.0),
        "initial_sufficiency_score": initial["score"],
        "final_sufficiency_score": final["score"],
        "initial_sufficiency_label": initial["label"],
        "final_sufficiency_label": final["label"],
        "initial_failure_reason": payload["repair_rounds"][0]["diagnosis"]["reason"]
        if payload["repair_rounds"]
        else final_diagnosis["reason"],
        "final_failure_reason": final_diagnosis["reason"],
        "repair_round_count": payload["repair_round_count"],
        "repair_success": repair_success,
        "recovery": recovery,
        "stop_reason": payload["stop_reason"],
        "repair_actions": [
            repair_round["selected_action"]["action"]
            for repair_round in payload["repair_rounds"]
        ],
        "evidence": [
            {
                "document_id": document_id,
                "node_id": citation["node_id"],
                "page_number": citation["page_number"],
                "bbox": citation["bbox"],
            }
            for citation in payload["citations"]
        ],
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_strategy.setdefault(result["strategy"], []).append(result)
    metrics: dict[str, Any] = {}
    for strategy, rows in by_strategy.items():
        metrics[strategy] = {
            "case_count": len(rows),
            "answer_term_hit_rate": round(mean(row["answer_term_hit"] for row in rows), 4),
            "citation_node_type_hit_rate": round(mean(row["citation_node_type_hit"] for row in rows), 4),
            "claim_supported_rate": round(mean(row["claim_supported"] for row in rows), 4),
            "average_tool_calls": round(mean(row["tool_calls"] for row in rows), 4),
            "average_latency_ms": round(mean(row["latency_ms"] for row in rows), 4),
        }
        if any("evidence_pack_context_hit" in row for row in rows):
            metrics[strategy]["evidence_pack_context_hit_rate"] = round(
                mean(row.get("evidence_pack_context_hit", 0.0) for row in rows),
                4,
            )
        if any("repair_round_count" in row for row in rows):
            metrics[strategy]["initial_sufficiency_score"] = round(
                mean(row.get("initial_sufficiency_score", 0.0) for row in rows),
                4,
            )
            metrics[strategy]["final_sufficiency_score"] = round(
                mean(row.get("final_sufficiency_score", 0.0) for row in rows),
                4,
            )
            metrics[strategy]["average_repair_rounds"] = round(
                mean(row.get("repair_round_count", 0.0) for row in rows),
                4,
            )
            metrics[strategy]["repair_success_rate"] = round(
                mean(row.get("repair_success", 0.0) for row in rows),
                4,
            )
            metrics[strategy]["recovery_rate"] = round(
                mean(row.get("recovery", 0.0) for row in rows),
                4,
            )
    return metrics


def reliability_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    v3_rows = [result for result in results if result.get("strategy") == "v3_self_correcting"]
    before: dict[str, int] = {}
    after: dict[str, int] = {}
    for row in v3_rows:
        before_reason = str(row.get("initial_failure_reason") or "unknown")
        after_reason = str(row.get("final_failure_reason") or "unknown")
        before[before_reason] = before.get(before_reason, 0) + 1
        after[after_reason] = after.get(after_reason, 0) + 1
    return {
        "case_count": len(v3_rows),
        "repair_case_count": sum(1 for row in v3_rows if row.get("repair_round_count", 0) > 0),
        "recovery_rate": round(mean(row.get("recovery", 0.0) for row in v3_rows), 4)
        if v3_rows
        else 0.0,
        "repair_success_rate": round(mean(row.get("repair_success", 0.0) for row in v3_rows), 4)
        if v3_rows
        else 0.0,
        "average_repair_rounds": round(mean(row.get("repair_round_count", 0.0) for row in v3_rows), 4)
        if v3_rows
        else 0.0,
        "failure_before_distribution": dict(sorted(before.items())),
        "failure_after_distribution": dict(sorted(after.items())),
    }


def markdown_report(report: dict[str, Any]) -> str:
    title = "MAGE-Doc V3 Reliability Report" if "reliability_summary" in report else "MAGE-Doc V2 Evaluation Report"
    lines = [f"# {title}", ""]
    lines.append(f"Case count: {report['case_count']}")
    lines.append("")
    lines.append("| Strategy | Answer term hit | Citation type hit | Claim supported | Avg tool calls | Avg latency ms |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for strategy, metrics in report["metrics"].items():
        lines.append(
            "| {strategy} | {answer:.2f} | {citation:.2f} | {claim:.2f} | {tools:.2f} | {latency:.2f} |".format(
                strategy=strategy,
                answer=metrics["answer_term_hit_rate"],
                citation=metrics["citation_node_type_hit_rate"],
                claim=metrics["claim_supported_rate"],
                tools=metrics["average_tool_calls"],
                latency=metrics["average_latency_ms"],
            )
        )
    lines.append("")
    failure_summary = report.get("failure_summary", {})
    distribution = failure_summary.get("distribution", {})
    if distribution:
        lines.append("## Failure Diagnosis")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("| --- | --- |")
        for reason, count in distribution.items():
            lines.append(f"| {reason} | {count} |")
        lines.append("")
    reliability = report.get("reliability_summary", {})
    if reliability:
        lines.append("## Reliability Summary")
        lines.append("")
        lines.append(f"Repair cases: {reliability['repair_case_count']} / {reliability['case_count']}")
        lines.append(f"Recovery rate: {reliability['recovery_rate']:.2f}")
        lines.append(f"Repair success rate: {reliability['repair_success_rate']:.2f}")
        lines.append(f"Average repair rounds: {reliability['average_repair_rounds']:.2f}")
        lines.append("")
        lines.append("### Failure Before")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("| --- | --- |")
        for reason, count in reliability.get("failure_before_distribution", {}).items():
            lines.append(f"| {reason} | {count} |")
        lines.append("")
        lines.append("### Failure After")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("| --- | --- |")
        for reason, count in reliability.get("failure_after_distribution", {}).items():
            lines.append(f"| {reason} | {count} |")
        lines.append("")
        v3_rows = [row for row in report.get("results", []) if row.get("strategy") == "v3_self_correcting"]
        if v3_rows:
            lines.append("## V3 Repair Cases")
            lines.append("")
            lines.append("| Case | Initial | Final | Rounds | Actions |")
            lines.append("| --- | --- | --- | --- | --- |")
            for row in v3_rows:
                lines.append(
                    "| {case} | {initial:.2f} | {final:.2f} | {rounds} | {actions} |".format(
                        case=row["case_id"],
                        initial=row.get("initial_sufficiency_score", 0.0),
                        final=row.get("final_sufficiency_score", 0.0),
                        rounds=row.get("repair_round_count", 0),
                        actions=", ".join(row.get("repair_actions", [])) or "-",
                    )
                )
            lines.append("")
    return "\n".join(lines)


def run_eval(cases_path: Path = DEFAULT_CASES, output: Path | None = None) -> dict[str, Any]:
    cases = load_v3_cases(cases_path) if cases_path.name.startswith("v3_") else load_cases(cases_path)
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)
        client, engine = make_client(workdir)
        try:
            document = prepare_document(client)
            results: list[dict[str, Any]] = []
            prepare_v2_layers(client, document["id"])
            for case in cases:
                results.append(run_v0_agent_case(client, document["id"], case))
                results.append(run_v1_pack_case(client, document["id"], case))
                results.append(run_v2_multimodal_case(client, document["id"], case))
                results.append(run_v3_self_correcting_case(client, document["id"], case))
            report = {
                "case_count": len(cases),
                "result_count": len(results),
                "metrics": aggregate(results),
                "failure_summary": diagnose_results(cases, results),
                "v3_failure_taxonomy": diagnose_failures(cases, results),
                "reliability_summary": reliability_summary(results),
                "curated_failure_targets": curated_benchmark.case_failure_targets(cases),
                "results": results,
            }
        finally:
            client.close()
            app.dependency_overrides.clear()
            engine.dispose()
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        output.with_suffix(".md").write_text(markdown_report(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_V3_CASES)
    parser.add_argument("--output", type=Path, default=ROOT / "eval" / "reports" / "v3_reliability_report.json")
    args = parser.parse_args()
    report = run_eval(cases_path=args.cases, output=args.output)
    print(json.dumps({"case_count": report["case_count"], "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
