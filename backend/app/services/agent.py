import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.documents import get_document
from app.services.retrieval import (
    inspect_page_tool,
    read_table_tool,
    search_evidence,
    verify_answer_tool,
)
from app.services.trace_store import (
    complete_trace_run,
    create_trace_run,
    fail_trace_run,
    record_tool_call,
)

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


def _classify_question(question: str) -> str:
    normalized = question.lower()
    if any(keyword in normalized for keyword in TABLE_KEYWORDS):
        return "table_lookup"
    if re.search(r"\d", normalized):
        return "table_lookup"
    return "text_lookup"


def _citation_from_result(result: dict, snippet: str | None = None) -> dict:
    node = result["node"]
    return {
        "node_id": node["id"],
        "node_type": node["node_type"],
        "page_number": node["page_number"],
        "bbox": node["bbox"],
        "snippet": snippet or result["snippet"],
    }


def _row_matches_question(row: list[str | None], question: str) -> bool:
    row_text = " ".join(str(cell or "").lower() for cell in row)
    terms = [
        term.lower()
        for term in re.findall(r"[A-Za-z0-9_]+", question)
        if not term.isdigit()
    ]
    return any(term in row_text for term in terms)


def _select_table_row(matrix: list[list[str | None]], question: str) -> list[str | None] | None:
    for row in matrix:
        if _row_matches_question(row, question):
            return row
    return matrix[0] if matrix else None


def _row_text(row: list[str | None]) -> str:
    return " | ".join(str(cell or "").strip() for cell in row)


def _empty_answer(
    trace_id: str,
    document_id: str,
    question: str,
    question_type: str,
    trace: list[dict],
    verification: dict,
) -> dict:
    return {
        "trace_id": trace_id,
        "document_id": document_id,
        "question": question,
        "question_type": question_type,
        "answer": "I could not find supporting evidence for this question in the parsed document.",
        "citations": [],
        "trace": trace,
        "verification": verification,
    }


def _append_trace(
    db: Session,
    *,
    document_id: str,
    trace_run_id: str,
    trace: list[dict],
    payload: dict,
) -> None:
    tool_trace = payload.get("tool_trace")
    if isinstance(tool_trace, dict):
        trace.append(tool_trace)
        record_tool_call(
            db,
            trace_run_id=trace_run_id,
            document_id=document_id,
            step_index=len(trace),
            tool_trace=tool_trace,
        )


def answer_question(db: Session, document_id: str, question: str) -> dict:
    clean_question = question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required",
        )
    get_document(db, document_id)

    question_type = _classify_question(clean_question)
    trace_run = create_trace_run(
        db,
        document_id=document_id,
        question=clean_question,
        question_type=question_type,
        metadata={"agent": "deterministic_v1_phase5"},
    )
    primary_node_types = "table" if question_type == "table_lookup" else "text_block"
    trace: list[dict] = []

    try:
        search_payload = search_evidence(
            db,
            document_id,
            query=clean_question,
            top_k=3,
            node_types=primary_node_types,
        )
        _append_trace(
            db,
            document_id=document_id,
            trace_run_id=trace_run.id,
            trace=trace,
            payload=search_payload,
        )
        results = search_payload["results"]
        if not results:
            fallback_payload = search_evidence(
                db,
                document_id,
                query=clean_question,
                top_k=3,
                node_types=None,
            )
            _append_trace(
                db,
                document_id=document_id,
                trace_run_id=trace_run.id,
                trace=trace,
                payload=fallback_payload,
            )
            results = fallback_payload["results"]

        if not results:
            verification = verify_answer_tool(db, document_id, answer="", citation_node_ids=[])
            _append_trace(
                db,
                document_id=document_id,
                trace_run_id=trace_run.id,
                trace=trace,
                payload=verification,
            )
            complete_trace_run(
                db,
                trace_run.id,
                answer="",
                metadata={"result": "no_supporting_evidence"},
            )
            return _empty_answer(
                trace_run.id,
                document_id,
                clean_question,
                question_type,
                trace,
                verification,
            )

        top_result = results[0]
        top_node = top_result["node"]
        citations: list[dict] = []

        if top_node["node_type"] == "table":
            table_payload = read_table_tool(db, document_id, top_node["id"])
            _append_trace(
                db,
                document_id=document_id,
                trace_run_id=trace_run.id,
                trace=trace,
                payload=table_payload,
            )
            row = _select_table_row(table_payload["matrix"], clean_question)
            table_snippet = _row_text(row) if row else top_result["snippet"]
            answer = (
                f"Based on table evidence on page {top_node['page_number']}, "
                f"the most relevant row is: {table_snippet}."
            )
            citations.append(_citation_from_result(top_result, table_snippet))
        else:
            page_payload = inspect_page_tool(db, document_id, top_node["page_number"])
            _append_trace(
                db,
                document_id=document_id,
                trace_run_id=trace_run.id,
                trace=trace,
                payload=page_payload,
            )
            answer = (
                f"Based on text evidence on page {top_node['page_number']}, "
                f"{top_result['snippet']}"
            )
            citations.append(_citation_from_result(top_result))

        verification = verify_answer_tool(
            db,
            document_id,
            answer=answer,
            citation_node_ids=[citation["node_id"] for citation in citations],
        )
        _append_trace(
            db,
            document_id=document_id,
            trace_run_id=trace_run.id,
            trace=trace,
            payload=verification,
        )
        complete_trace_run(
            db,
            trace_run.id,
            answer=answer,
            metadata={
                "result": "answered",
                "citation_count": len(citations),
                "verification_passed": verification["passed"],
            },
        )

        return {
            "trace_id": trace_run.id,
            "document_id": document_id,
            "question": clean_question,
            "question_type": question_type,
            "answer": answer,
            "citations": citations,
            "trace": trace,
            "verification": verification,
        }
    except Exception as exc:
        fail_trace_run(db, trace_run.id, error=str(exc))
        raise
