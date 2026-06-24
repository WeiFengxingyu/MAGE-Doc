from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvidenceNodeResponse(BaseModel):
    id: str
    document_id: str
    page_id: str
    page_number: int
    node_type: str
    text: str
    bbox: list[float]
    reading_order: int
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
