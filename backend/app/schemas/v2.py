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
