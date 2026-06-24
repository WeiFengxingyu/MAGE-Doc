from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ToolDefinitionResponse(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    phase: str


class AgentToolCallResponse(BaseModel):
    id: str
    trace_run_id: str
    document_id: str
    step_index: int
    tool_name: str
    input: dict[str, Any]
    output_summary: str
    latency_ms: int
    status: str
    metadata: dict[str, Any]
    created_at: datetime


class AgentTraceRunSummaryResponse(BaseModel):
    id: str
    document_id: str
    question: str
    question_type: str
    status: str
    answer_preview: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tool_call_count: int


class AgentTraceRunDetailResponse(AgentTraceRunSummaryResponse):
    tool_calls: list[AgentToolCallResponse]
