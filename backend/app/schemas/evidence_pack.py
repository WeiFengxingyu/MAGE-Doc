from typing import Any

from pydantic import BaseModel

from app.schemas.evidence import EvidenceNodeResponse
from app.schemas.graph import EvidenceEdgeResponse
from app.schemas.tools import ToolTraceResponse


class EvidencePackCandidateResponse(BaseModel):
    rank: int
    score: float
    matched_terms: list[str]
    snippet: str
    node: EvidenceNodeResponse
    retrieval_source: str
    candidate_sources: list[str]
    score_breakdown: dict[str, float]


class EvidencePackItemResponse(BaseModel):
    node: EvidenceNodeResponse
    source_candidate_node_id: str
    source_candidate_rank: int
    graph_distance: int
    inclusion_reason: str
    path: list[EvidenceEdgeResponse]
    score_breakdown: dict[str, float]
    metadata: dict[str, Any]


class EvidencePackSummaryResponse(BaseModel):
    source_candidate_count: int
    expanded_node_count: int
    edge_count: int
    item_count: int
    max_graph_distance: int
    edge_type_counts: dict[str, int]
    node_type_counts: dict[str, int]


class EvidencePackResponse(BaseModel):
    query: str
    document_id: str
    source_candidates: list[EvidencePackCandidateResponse]
    nodes: list[EvidenceNodeResponse]
    edges: list[EvidenceEdgeResponse]
    items: list[EvidencePackItemResponse]
    summary: EvidencePackSummaryResponse
    tool_trace: ToolTraceResponse
