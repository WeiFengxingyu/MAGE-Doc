from typing import Any

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceNodeResponse


class ToolTraceResponse(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output_summary: str
    latency_ms: int


class SearchResultResponse(BaseModel):
    rank: int
    score: float
    matched_terms: list[str]
    snippet: str
    node: EvidenceNodeResponse
    retrieval_source: str = "lexical"
    candidate_sources: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    document_id: str
    results: list[SearchResultResponse]
    tool_trace: ToolTraceResponse


class PageEvidenceSummary(BaseModel):
    node_id: str
    node_type: str
    bbox: list[float]
    reading_order: int
    snippet: str


class InspectPageResponse(BaseModel):
    document_id: str
    page_id: str
    page_number: int
    width: float
    height: float
    image_url: str
    evidence_count: int
    evidence: list[PageEvidenceSummary]
    tool_trace: ToolTraceResponse


class ReadTableResponse(BaseModel):
    document_id: str
    table_id: str
    page_number: int
    bbox: list[float]
    row_count: int
    col_count: int
    matrix: list[list[str | None]]
    cells: list[list[float]]
    text: str
    tool_trace: ToolTraceResponse


class VerifyAnswerRequest(BaseModel):
    answer: str = Field(default="")
    citation_node_ids: list[str] = Field(default_factory=list)


class VerifyAnswerResponse(BaseModel):
    document_id: str
    passed: bool
    answer_present: bool
    citation_count: int
    covered_citation_node_ids: list[str]
    missing_citation_node_ids: list[str]
    tool_trace: ToolTraceResponse
