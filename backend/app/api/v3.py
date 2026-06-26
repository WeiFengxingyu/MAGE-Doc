from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.v3 import (
    FailureTaxonomyRequest,
    FailureTaxonomyResponse,
    RepairPlanRequest,
    RepairPlanResponse,
    SelfCorrectingQuestionRequest,
    SelfCorrectingQuestionResponse,
    SufficiencyScoreRequest,
    SufficiencyScoreResponse,
)
from app.services.v3_failure_taxonomy import diagnose_failures
from app.services.v3_repair_policy import build_repair_plan
from app.services.v3_self_correcting_agent import answer_self_correcting_question
from app.services.v3_sufficiency import score_evidence

router = APIRouter(prefix="/api/v3", tags=["v3"])


@router.post("/failure-taxonomy", response_model=FailureTaxonomyResponse)
def failure_taxonomy(payload: FailureTaxonomyRequest) -> FailureTaxonomyResponse:
    return diagnose_failures(payload.cases, payload.results)


@router.post("/sufficiency-score", response_model=SufficiencyScoreResponse)
def sufficiency_score(payload: SufficiencyScoreRequest) -> SufficiencyScoreResponse:
    return score_evidence(payload.case, payload.result)


@router.post("/repair-plan", response_model=RepairPlanResponse)
def repair_plan(payload: RepairPlanRequest) -> RepairPlanResponse:
    return build_repair_plan(
        payload.diagnoses,
        max_actions_per_diagnosis=payload.max_actions_per_diagnosis,
    )


@router.post(
    "/documents/{document_id}/self-correcting-questions",
    response_model=SelfCorrectingQuestionResponse,
)
def self_correcting_question(
    document_id: str,
    payload: SelfCorrectingQuestionRequest,
    db: Session = Depends(get_db),
) -> SelfCorrectingQuestionResponse:
    return answer_self_correcting_question(
        db,
        document_id,
        payload.question,
        max_repair_rounds=payload.max_repair_rounds,
    )

