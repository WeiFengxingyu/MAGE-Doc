from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.v2 import CollectionCreateRequest, CollectionResponse, CollectionSearchResponse
from app.services.v2_collections import (
    add_document_to_collection,
    create_collection,
    list_collections,
    search_collection,
)

router = APIRouter(prefix="/api/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection_endpoint(
    payload: CollectionCreateRequest,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    return create_collection(db, payload.name, payload.description)


@router.get("", response_model=list[CollectionResponse])
def list_collections_endpoint(db: Session = Depends(get_db)) -> list[CollectionResponse]:
    return list_collections(db)


@router.post("/{collection_id}/documents/{document_id}", response_model=CollectionResponse)
def add_document_endpoint(
    collection_id: str,
    document_id: str,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    return add_document_to_collection(db, collection_id, document_id)


@router.get("/{collection_id}/search", response_model=CollectionSearchResponse)
def collection_search_endpoint(
    collection_id: str,
    query: str,
    top_k: int = 5,
    node_types: str | None = None,
    db: Session = Depends(get_db),
) -> CollectionSearchResponse:
    return search_collection(db, collection_id, query=query, top_k=top_k, node_types=node_types)
