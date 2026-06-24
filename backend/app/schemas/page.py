from datetime import datetime

from pydantic import BaseModel


class PageResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    width: float
    height: float
    image_width: int
    image_height: int
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}
