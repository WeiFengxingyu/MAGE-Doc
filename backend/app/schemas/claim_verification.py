from pydantic import BaseModel, Field

from app.schemas.tools import ToolTraceResponse


class ClaimVerificationItemResponse(BaseModel):
    claim: str
    status: str
    citation_node_ids: list[str]
    reason: str
    matched_terms: list[str] = Field(default_factory=list)
    missing_terms: list[str] = Field(default_factory=list)
    required_node_types: list[str] = Field(default_factory=list)


class ClaimVerificationResponse(BaseModel):
    status: str
    claim_count: int
    supported_count: int
    partial_count: int
    unsupported_count: int
    insufficient_evidence_count: int
    claims: list[ClaimVerificationItemResponse]
    tool_trace: ToolTraceResponse
