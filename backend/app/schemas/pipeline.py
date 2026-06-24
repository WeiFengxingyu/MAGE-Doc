from pydantic import BaseModel


class PipelineStepResponse(BaseModel):
    name: str
    status: str
    output_summary: str


class PrepareDemoResponse(BaseModel):
    document_id: str
    status: str
    page_count: int
    text_block_count: int
    table_count: int
    steps: list[PipelineStepResponse]
