from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.evidence import EvidenceNodeResponse


class EvidenceEdgeResponse(BaseModel):
    id: str
    document_id: str
    source_node_id: str | None
    target_node_id: str
    edge_type: str
    weight: float
    source: str
    metadata: dict[str, Any]
    created_at: datetime


class GraphBuildResponse(BaseModel):
    document_id: str
    node_count: int
    edge_count: int
    created_edge_count: int
    edge_type_counts: dict[str, int]


class DocumentGraphResponse(BaseModel):
    document_id: str
    node_count: int
    edge_count: int
    edge_type_counts: dict[str, int]
    nodes: list[EvidenceNodeResponse]
    edges: list[EvidenceEdgeResponse]


class NodeNeighborsResponse(BaseModel):
    document_id: str
    node: EvidenceNodeResponse
    incoming_edges: list[EvidenceEdgeResponse]
    outgoing_edges: list[EvidenceEdgeResponse]
    incoming_nodes: list[EvidenceNodeResponse]
    outgoing_nodes: list[EvidenceNodeResponse]
