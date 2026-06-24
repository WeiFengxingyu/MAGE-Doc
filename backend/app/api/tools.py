from fastapi import APIRouter

from app.schemas.trace import ToolDefinitionResponse
from app.services.tool_registry import list_registered_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=list[ToolDefinitionResponse])
def tools() -> list[ToolDefinitionResponse]:
    return list_registered_tools()
