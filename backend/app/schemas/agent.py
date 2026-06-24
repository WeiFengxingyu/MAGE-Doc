from pydantic import BaseModel, Field

from app.schemas.tools import ToolTraceResponse, VerifyAnswerResponse


class QuestionRequest(BaseModel):
    question: str = Field(default="")


class CitationResponse(BaseModel):
    node_id: str
    node_type: str
    page_number: int
    bbox: list[float]
    snippet: str


class QuestionAnswerResponse(BaseModel):
    trace_id: str | None = None
    document_id: str
    question: str
    question_type: str
    answer: str
    citations: list[CitationResponse]
    trace: list[ToolTraceResponse]
    verification: VerifyAnswerResponse
