import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.trace import AgentToolCall, AgentTraceRun
from app.services.documents import get_document
from app.services.evidence import _json_loads


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _run_to_summary(run: AgentTraceRun) -> dict:
    return {
        "id": run.id,
        "document_id": run.document_id,
        "question": run.question,
        "question_type": run.question_type,
        "status": run.status,
        "answer_preview": run.answer_preview,
        "metadata": _json_loads(run.metadata_json, {}),
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "tool_call_count": len(run.tool_calls),
    }


def _tool_call_to_response(call: AgentToolCall) -> dict:
    return {
        "id": call.id,
        "trace_run_id": call.trace_run_id,
        "document_id": call.document_id,
        "step_index": call.step_index,
        "tool_name": call.tool_name,
        "input": _json_loads(call.input_json, {}),
        "output_summary": call.output_summary,
        "latency_ms": call.latency_ms,
        "status": call.status,
        "metadata": _json_loads(call.metadata_json, {}),
        "created_at": call.created_at,
    }


def create_trace_run(
    db: Session,
    *,
    document_id: str,
    question: str,
    question_type: str,
    metadata: dict[str, Any] | None = None,
) -> AgentTraceRun:
    run = AgentTraceRun(
        document_id=document_id,
        question=question,
        question_type=question_type,
        status="running",
        metadata_json=_json_dumps(metadata or {}),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def record_tool_call(
    db: Session,
    *,
    trace_run_id: str,
    document_id: str,
    step_index: int,
    tool_trace: dict[str, Any],
    status_value: str = "completed",
    metadata: dict[str, Any] | None = None,
) -> AgentToolCall:
    call = AgentToolCall(
        trace_run_id=trace_run_id,
        document_id=document_id,
        step_index=step_index,
        tool_name=str(tool_trace.get("tool_name", "")),
        input_json=_json_dumps(tool_trace.get("input", {})),
        output_summary=str(tool_trace.get("output_summary", "")),
        latency_ms=int(tool_trace.get("latency_ms") or 0),
        status=status_value,
        metadata_json=_json_dumps(metadata or {}),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def complete_trace_run(
    db: Session,
    trace_run_id: str,
    *,
    answer: str,
    status_value: str = "completed",
    metadata: dict[str, Any] | None = None,
) -> AgentTraceRun:
    run = db.get(AgentTraceRun, trace_run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace run not found")
    run.status = status_value
    run.answer_preview = answer.strip()[:300] if answer.strip() else None
    if metadata is not None:
        run.metadata_json = _json_dumps(metadata)
    db.commit()
    db.refresh(run)
    return run


def fail_trace_run(
    db: Session,
    trace_run_id: str,
    *,
    error: str,
) -> None:
    run = db.get(AgentTraceRun, trace_run_id)
    if run is None:
        return
    run.status = "failed"
    metadata = _json_loads(run.metadata_json, {})
    metadata["error"] = error
    run.metadata_json = _json_dumps(metadata)
    db.commit()


def list_trace_runs(db: Session, document_id: str) -> list[dict]:
    get_document(db, document_id)
    runs = (
        db.query(AgentTraceRun)
        .options(joinedload(AgentTraceRun.tool_calls))
        .filter(AgentTraceRun.document_id == document_id)
        .order_by(AgentTraceRun.created_at.desc())
        .all()
    )
    return [_run_to_summary(run) for run in runs]


def get_trace_run_detail(db: Session, document_id: str, trace_id: str) -> dict:
    get_document(db, document_id)
    run = (
        db.query(AgentTraceRun)
        .options(joinedload(AgentTraceRun.tool_calls))
        .filter(AgentTraceRun.document_id == document_id, AgentTraceRun.id == trace_id)
        .one_or_none()
    )
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace run not found")
    tool_calls = sorted(run.tool_calls, key=lambda call: call.step_index)
    return {
        **_run_to_summary(run),
        "tool_calls": [_tool_call_to_response(call) for call in tool_calls],
    }
