from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.schemas.evidence import EvidenceNodeResponse
from app.schemas.page import PageResponse
from app.schemas.tools import (
    InspectPageResponse,
    ReadTableResponse,
    SearchResponse,
    VerifyAnswerRequest,
    VerifyAnswerResponse,
)
from app.services.documents import create_document, get_document, list_documents
from app.services.evidence import (
    list_document_tables,
    list_document_text_blocks,
    list_page_tables,
    list_page_text_blocks,
    parse_document_tables,
    parse_document_text_blocks,
)
from app.services.pages import (
    get_page_image_path,
    get_page_response,
    list_pages,
    render_document_pages,
)
from app.services.retrieval import (
    inspect_page_tool,
    read_table_tool,
    search_evidence,
    verify_answer_tool,
)

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


@router.get("/{document_id}/search", response_model=SearchResponse)
def document_search(
    document_id: str,
    query: str,
    top_k: int = 5,
    node_types: str | None = None,
    db: Session = Depends(get_db),
) -> SearchResponse:
    return search_evidence(db, document_id, query=query, top_k=top_k, node_types=node_types)


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
