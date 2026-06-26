from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.evidence import EvidenceNodeResponse
from app.schemas.evidence_pack import EvidencePackResponse
from app.schemas.agent import QuestionAnswerResponse, QuestionRequest
from app.schemas.graph import DocumentGraphResponse, GraphBuildResponse, NodeNeighborsResponse
from app.schemas.page import PageResponse
from app.schemas.pipeline import PrepareDemoResponse
from app.schemas.trace import AgentTraceRunDetailResponse, AgentTraceRunSummaryResponse
from app.schemas.v2 import MetricGraphResponse, OcrPipelineResponse, OcrRunResponse, VisionGroundingResponse
from app.schemas.tools import (
    InspectPageResponse,
    ReadTableResponse,
    SearchResponse,
    VerifyAnswerRequest,
    VerifyAnswerResponse,
)
from app.services.documents import create_document, get_document, list_documents
from app.services.agent import answer_question
from app.services.evidence import (
    list_document_tables,
    list_document_text_blocks,
    list_page_tables,
    list_page_text_blocks,
    parse_document_tables,
    parse_document_text_blocks,
)
from app.services.evidence_pack import build_evidence_pack
from app.services.graph import build_document_graph, get_node_neighbors, list_document_graph
from app.services.pages import (
    get_page_image_path,
    get_page_response,
    list_pages,
    render_document_pages,
)
from app.services.pipeline import prepare_document_demo
from app.services.retrieval import (
    inspect_page_tool,
    read_table_tool,
    search_evidence,
    verify_answer_tool,
)
from app.services.trace_store import get_trace_run_detail, list_trace_runs
from app.services.v2_ocr import list_ocr_runs, list_ocr_text_blocks, run_document_ocr
from app.services.v2_metric import build_metric_graph, list_metric_values
from app.services.v2_vision import list_visual_nodes, run_vision_grounding

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return await create_document(db=db, file=file)


@router.get("", response_model=list[DocumentResponse])
def documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    return list_documents(db)


@router.get("/{document_id}", response_model=DocumentResponse)
def document_detail(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return get_document(db, document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentStatusResponse:
    return get_document(db, document_id)


@router.post("/{document_id}/render", response_model=list[PageResponse])
def render_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[PageResponse]:
    return render_document_pages(db, document_id)


@router.post("/{document_id}/prepare-demo", response_model=PrepareDemoResponse)
def prepare_demo(
    document_id: str,
    db: Session = Depends(get_db),
) -> PrepareDemoResponse:
    return prepare_document_demo(db, document_id)


@router.post("/{document_id}/parse-text", response_model=list[EvidenceNodeResponse])
def parse_document_text(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return parse_document_text_blocks(db, document_id)


@router.post("/{document_id}/parse-tables", response_model=list[EvidenceNodeResponse])
def parse_document_table_nodes(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return parse_document_tables(db, document_id)


@router.get("/{document_id}/text-blocks", response_model=list[EvidenceNodeResponse])
def document_text_blocks(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_document_text_blocks(db, document_id)


@router.get("/{document_id}/tables", response_model=list[EvidenceNodeResponse])
def document_tables(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_document_tables(db, document_id)


@router.post("/{document_id}/ocr", response_model=OcrPipelineResponse)
def run_ocr(
    document_id: str,
    min_text_chars: int = 20,
    db: Session = Depends(get_db),
) -> OcrPipelineResponse:
    return run_document_ocr(db, document_id, min_text_chars=min_text_chars)


@router.get("/{document_id}/ocr-runs", response_model=list[OcrRunResponse])
def document_ocr_runs(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[OcrRunResponse]:
    return list_ocr_runs(db, document_id)


@router.get("/{document_id}/ocr-text-blocks", response_model=list[EvidenceNodeResponse])
def document_ocr_text_blocks(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_ocr_text_blocks(db, document_id)


@router.post("/{document_id}/vision-grounding", response_model=VisionGroundingResponse)
def vision_grounding(
    document_id: str,
    db: Session = Depends(get_db),
) -> VisionGroundingResponse:
    return run_vision_grounding(db, document_id)


@router.get("/{document_id}/visual-nodes", response_model=list[EvidenceNodeResponse])
def document_visual_nodes(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_visual_nodes(db, document_id)


@router.post("/{document_id}/metric-graph/build", response_model=MetricGraphResponse)
def metric_graph_build(
    document_id: str,
    db: Session = Depends(get_db),
) -> MetricGraphResponse:
    return build_metric_graph(db, document_id)


@router.get("/{document_id}/metric-values", response_model=list[EvidenceNodeResponse])
def document_metric_values(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_metric_values(db, document_id)


@router.get("/{document_id}/search", response_model=SearchResponse)
def document_search(
    document_id: str,
    query: str,
    top_k: int = 5,
    node_types: str | None = None,
    db: Session = Depends(get_db),
) -> SearchResponse:
    return search_evidence(db, document_id, query=query, top_k=top_k, node_types=node_types)


@router.post("/{document_id}/graph/build", response_model=GraphBuildResponse)
def build_graph(
    document_id: str,
    db: Session = Depends(get_db),
) -> GraphBuildResponse:
    return build_document_graph(db, document_id)


@router.get("/{document_id}/graph", response_model=DocumentGraphResponse)
def document_graph(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentGraphResponse:
    return list_document_graph(db, document_id)


@router.get("/{document_id}/graph/neighbors/{node_id}", response_model=NodeNeighborsResponse)
def graph_neighbors(
    document_id: str,
    node_id: str,
    db: Session = Depends(get_db),
) -> NodeNeighborsResponse:
    return get_node_neighbors(db, document_id, node_id)


@router.get("/{document_id}/evidence-pack", response_model=EvidencePackResponse)
def document_evidence_pack(
    document_id: str,
    query: str,
    top_k: int = 3,
    depth: int = 1,
    node_types: str | None = None,
    edge_types: str | None = None,
    db: Session = Depends(get_db),
) -> EvidencePackResponse:
    return build_evidence_pack(
        db,
        document_id,
        query=query,
        top_k=top_k,
        depth=depth,
        node_types=node_types,
        edge_types=edge_types,
    )


@router.get("/{document_id}/traces", response_model=list[AgentTraceRunSummaryResponse])
def document_traces(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[AgentTraceRunSummaryResponse]:
    return list_trace_runs(db, document_id)


@router.get("/{document_id}/traces/{trace_id}", response_model=AgentTraceRunDetailResponse)
def document_trace_detail(
    document_id: str,
    trace_id: str,
    db: Session = Depends(get_db),
) -> AgentTraceRunDetailResponse:
    return get_trace_run_detail(db, document_id, trace_id)


@router.post("/{document_id}/questions", response_model=QuestionAnswerResponse)
def ask_document_question(
    document_id: str,
    payload: QuestionRequest,
    db: Session = Depends(get_db),
) -> QuestionAnswerResponse:
    return answer_question(db, document_id, payload.question)


@router.get("/{document_id}/pages", response_model=list[PageResponse])
def document_pages(
    document_id: str,
    db: Session = Depends(get_db),
) -> list[PageResponse]:
    return list_pages(db, document_id)


@router.get("/{document_id}/pages/{page_number}", response_model=PageResponse)
def document_page(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
) -> PageResponse:
    return get_page_response(db, document_id, page_number)


@router.get("/{document_id}/pages/{page_number}/image")
def document_page_image(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(get_page_image_path(db, document_id, page_number), media_type="image/png")


@router.get(
    "/{document_id}/pages/{page_number}/text-blocks",
    response_model=list[EvidenceNodeResponse],
)
def document_page_text_blocks(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_page_text_blocks(db, document_id, page_number)


@router.get(
    "/{document_id}/pages/{page_number}/tables",
    response_model=list[EvidenceNodeResponse],
)
def document_page_tables(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
) -> list[EvidenceNodeResponse]:
    return list_page_tables(db, document_id, page_number)


@router.get(
    "/{document_id}/tools/inspect-page/{page_number}",
    response_model=InspectPageResponse,
)
def inspect_page(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
) -> InspectPageResponse:
    return inspect_page_tool(db, document_id, page_number)


@router.get(
    "/{document_id}/tools/read-table/{table_id}",
    response_model=ReadTableResponse,
)
def read_table(
    document_id: str,
    table_id: str,
    db: Session = Depends(get_db),
) -> ReadTableResponse:
    return read_table_tool(db, document_id, table_id)


@router.post(
    "/{document_id}/tools/verify-answer",
    response_model=VerifyAnswerResponse,
)
def verify_answer(
    document_id: str,
    payload: VerifyAnswerRequest,
    db: Session = Depends(get_db),
) -> VerifyAnswerResponse:
    return verify_answer_tool(
        db,
        document_id,
        answer=payload.answer,
        citation_node_ids=payload.citation_node_ids,
    )
