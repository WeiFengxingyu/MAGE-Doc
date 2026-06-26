from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agent import CitationResponse
from app.schemas.claim_verification import ClaimVerificationResponse
from app.schemas.tools import ToolTraceResponse, VerifyAnswerResponse


class V3DiagnosisResponse(BaseModel):
    case_id: str
    strategy: str
    reason: str
    severity: str
    confidence: float
    message: str
    signals: dict[str, float]
    repair_candidates: list[str]


class FailureTaxonomyRequest(BaseModel):
    cases: list[dict[str, Any]] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)


class FailureTaxonomyResponse(BaseModel):
    case_count: int
    result_count: int
    distribution: dict[str, int]
    failed_count: int
    passed_count: int
    diagnoses: list[V3DiagnosisResponse]


class SufficiencyScoreRequest(BaseModel):
    case: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class SufficiencyScoreResponse(BaseModel):
    score: float
    label: str
    signals: dict[str, float]
    missing_signals: list[str]
    recommended_policy: str | None = None


class RepairPlanRequest(BaseModel):
    diagnoses: list[dict[str, Any]] = Field(default_factory=list)
    max_actions_per_diagnosis: int = 2


class RepairPlanResponse(BaseModel):
    action_count: int
    actions: list[dict[str, Any]]
    has_repair: bool


class SelfCorrectingQuestionRequest(BaseModel):
    question: str = Field(default="")
    max_repair_rounds: int = 2


class RepairRoundResponse(BaseModel):
    round_index: int
    diagnosis: V3DiagnosisResponse
    repair_plan: RepairPlanResponse
    selected_action: dict[str, Any]
    before_sufficiency: SufficiencyScoreResponse
    after_sufficiency: SufficiencyScoreResponse


class SelfCorrectingQuestionResponse(BaseModel):
    trace_id: str | None = None
    document_id: str
    question: str
    question_type: str
    answer: str
    citations: list[CitationResponse]
    trace: list[ToolTraceResponse]
    verification: VerifyAnswerResponse
    claim_verification: ClaimVerificationResponse
    initial_sufficiency: SufficiencyScoreResponse
    final_sufficiency: SufficiencyScoreResponse
    final_diagnosis: V3DiagnosisResponse
    repair_round_count: int
    repair_rounds: list[RepairRoundResponse]
    stop_reason: str

