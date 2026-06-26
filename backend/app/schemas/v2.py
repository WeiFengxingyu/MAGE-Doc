from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceNodeResponse
from app.schemas.tools import SearchResultResponse, ToolTraceResponse


class OcrRunResponse(BaseModel):
    id: str
    document_id: str
    page_id: str
    page_number: int
    status: str
    adapter: str
    text_block_count: int
    average_confidence: float
    metadata: dict[str, Any]
    created_at: datetime


class OcrPipelineResponse(BaseModel):
    document_id: str
    page_count: int
    ocr_run_count: int
    ocr_text_block_count: int
    runs: list[OcrRunResponse]
    nodes: list[EvidenceNodeResponse]
    tool_trace: ToolTraceResponse


class VisionGroundingResponse(BaseModel):
    document_id: str
    visual_node_count: int
    created_edge_count: int
    nodes: list[EvidenceNodeResponse]
    tool_trace: ToolTraceResponse


class MetricGraphResponse(BaseModel):
    document_id: str
    metric_value_count: int
    created_edge_count: int
    nodes: list[EvidenceNodeResponse]
    tool_trace: ToolTraceResponse


class CollectionCreateRequest(BaseModel):
    name: str = Field(default="")
    description: str = Field(default="")


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: str
    document_count: int
    created_at: datetime


class CollectionSearchResultResponse(BaseModel):
    document_id: str
    filename: str
    result: SearchResultResponse


class CollectionSearchResponse(BaseModel):
    collection_id: str
    query: str
    results: list[CollectionSearchResultResponse]
    tool_trace: ToolTraceResponse


class McpToolResponse(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class McpCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class McpCallResponse(BaseModel):
    tool_name: str
    ok: bool
    content: list[dict[str, Any]]
    tool_trace: dict[str, Any]


class McpSmokeResponse(BaseModel):
    document_id: str
    tool_count: int
    called_tool_count: int
    called_tools: list[str]
    ok: bool
    calls: list[McpCallResponse]


class FailureDiagnosisRequest(BaseModel):
    cases: list[dict[str, Any]] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)


class FailureDiagnosisResponse(BaseModel):
    case_count: int
    result_count: int
    distribution: dict[str, int]
    failed_count: int
    passed_count: int
    diagnoses: list[dict[str, Any]]


class V2CapabilityResponse(BaseModel):
    name: str
    status: str
    phase: str
    evidence: str


class V2StatusResponse(BaseModel):
    version: str
    batch: str
    status: str
    capabilities: list[V2CapabilityResponse]
