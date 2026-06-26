import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.v2 import Collection, CollectionDocument
from app.services.documents import get_document
from app.services.retrieval import search_evidence


def _elapsed_ms(start: float) -> int:
    return max(0, int((time.perf_counter() - start) * 1000))


def _trace(tool_name: str, input_payload: dict[str, Any], output_summary: str, start: float) -> dict:
    return {
        "tool_name": tool_name,
        "input": input_payload,
        "output_summary": output_summary,
        "latency_ms": _elapsed_ms(start),
    }


def _collection_response(db: Session, collection: Collection) -> dict:
    count = (
        db.query(CollectionDocument)
        .filter(CollectionDocument.collection_id == collection.id)
        .count()
    )
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "document_count": count,
        "created_at": collection.created_at,
    }


def create_collection(db: Session, name: str, description: str = "") -> dict:
    clean_name = name.strip() or "Untitled collection"
    collection = Collection(name=clean_name, description=description.strip())
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return _collection_response(db, collection)


def list_collections(db: Session) -> list[dict]:
    collections = db.query(Collection).order_by(Collection.created_at.desc()).all()
    return [_collection_response(db, collection) for collection in collections]


def add_document_to_collection(db: Session, collection_id: str, document_id: str) -> dict:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    get_document(db, document_id)
    existing = (
        db.query(CollectionDocument)
        .filter(
            CollectionDocument.collection_id == collection_id,
            CollectionDocument.document_id == document_id,
        )
        .one_or_none()
    )
    if existing is None:
        db.add(CollectionDocument(collection_id=collection_id, document_id=document_id))
        db.commit()
        db.refresh(collection)
    return _collection_response(db, collection)


def _collection_documents(db: Session, collection_id: str) -> list[Document]:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    memberships = (
        db.query(CollectionDocument)
        .filter(CollectionDocument.collection_id == collection_id)
        .all()
    )
    document_ids = [membership.document_id for membership in memberships]
    if not document_ids:
        return []
    return db.query(Document).filter(Document.id.in_(document_ids)).all()


def search_collection(
    db: Session,
    collection_id: str,
    query: str,
    top_k: int = 5,
    node_types: str | None = None,
) -> dict:
    start = time.perf_counter()
    documents = _collection_documents(db, collection_id)
    results: list[dict] = []
    per_document_k = max(1, min(top_k, 10))
    for document in documents:
        payload = search_evidence(
            db,
            document.id,
            query=query,
            top_k=per_document_k,
            node_types=node_types,
        )
        for result in payload["results"]:
            results.append(
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "result": result,
                }
            )
    results.sort(
        key=lambda item: (
            -float(item["result"]["score"]),
            item["filename"],
            item["result"]["node"]["page_number"],
            item["result"]["rank"],
        )
    )
    limited = results[: max(1, min(top_k, 20))]
    return {
        "collection_id": collection_id,
        "query": query,
        "results": limited,
        "tool_trace": _trace(
            "search_collection",
            {"collection_id": collection_id, "query": query, "top_k": top_k, "node_types": node_types},
            f"{len(limited)} collection results",
            start,
        ),
    }
