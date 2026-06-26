from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.claim_verification import verify_claims
from app.services.evidence_pack import build_evidence_pack
from app.services.retrieval import inspect_page_tool, read_table_tool, search_evidence


MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_doc",
        "description": "Search multimodal evidence nodes in one document.",
        "input_schema": {
            "document_id": "string",
            "query": "string",
            "top_k": "integer",
            "node_types": "string|null",
        },
    },
    {
        "name": "inspect_page",
        "description": "Inspect page dimensions and evidence node summaries.",
        "input_schema": {"document_id": "string", "page_number": "integer"},
    },
    {
        "name": "read_table",
        "description": "Read a table evidence node as matrix and cells.",
        "input_schema": {"document_id": "string", "table_id": "string"},
    },
    {
        "name": "build_evidence_pack",
        "description": "Build a graph-expanded evidence pack for a query.",
        "input_schema": {
            "document_id": "string",
            "query": "string",
            "top_k": "integer",
            "depth": "integer",
            "node_types": "string|null",
            "edge_types": "string|null",
        },
    },
    {
        "name": "verify_claims",
        "description": "Verify generated claims against citation snippets.",
        "input_schema": {
            "document_id": "string",
            "answer": "string",
            "citations": "array",
            "question_type": "string",
        },
    },
]


def list_mcp_tools() -> list[dict[str, Any]]:
    return MCP_TOOLS


def _required_str(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required string argument: {key}",
        )
    return value.strip()


def _int_arg(arguments: dict[str, Any], key: str, default: int, minimum: int = 1) -> int:
    raw = arguments.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid integer argument: {key}",
        ) from exc
    return max(minimum, value)


def _optional_str(arguments: dict[str, Any], key: str) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid string argument: {key}",
        )
    clean = value.strip()
    return clean or None


def _tool_envelope(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "ok": True,
        "content": [{"type": "json", "json": payload}],
        "tool_trace": payload.get("tool_trace", {}),
    }


def call_mcp_tool(db: Session, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool_name = name.strip()
    if tool_name == "search_doc":
        document_id = _required_str(arguments, "document_id")
        payload = search_evidence(
            db,
            document_id,
            query=_required_str(arguments, "query"),
            top_k=_int_arg(arguments, "top_k", 5),
            node_types=_optional_str(arguments, "node_types"),
        )
        return _tool_envelope(tool_name, payload)

    if tool_name == "inspect_page":
        document_id = _required_str(arguments, "document_id")
        payload = inspect_page_tool(
            db,
            document_id,
            page_number=_int_arg(arguments, "page_number", 1),
        )
        return _tool_envelope(tool_name, payload)

    if tool_name == "read_table":
        document_id = _required_str(arguments, "document_id")
        payload = read_table_tool(db, document_id, _required_str(arguments, "table_id"))
        return _tool_envelope(tool_name, payload)

    if tool_name == "build_evidence_pack":
        document_id = _required_str(arguments, "document_id")
        payload = build_evidence_pack(
            db,
            document_id,
            query=_required_str(arguments, "query"),
            top_k=_int_arg(arguments, "top_k", 3),
            depth=_int_arg(arguments, "depth", 1, minimum=0),
            node_types=_optional_str(arguments, "node_types"),
            edge_types=_optional_str(arguments, "edge_types"),
        )
        return _tool_envelope(tool_name, payload)

    if tool_name == "verify_claims":
        document_id = _required_str(arguments, "document_id")
        citations = arguments.get("citations", [])
        if not isinstance(citations, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid citations argument: expected array",
            )
        payload = verify_claims(
            db,
            document_id,
            answer=_required_str(arguments, "answer"),
            citations=citations,
            question_type=str(arguments.get("question_type") or "text_lookup"),
        )
        return _tool_envelope(tool_name, payload)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown MCP tool: {name}")


def run_mcp_smoke(db: Session, document_id: str) -> dict[str, Any]:
    calls = [
        call_mcp_tool(
            db,
            "search_doc",
            {"document_id": document_id, "query": "revenue", "top_k": 3},
        ),
        call_mcp_tool(db, "inspect_page", {"document_id": document_id, "page_number": 1}),
        call_mcp_tool(
            db,
            "build_evidence_pack",
            {"document_id": document_id, "query": "revenue", "top_k": 2, "depth": 1},
        ),
    ]
    return {
        "document_id": document_id,
        "tool_count": len(MCP_TOOLS),
        "called_tool_count": len(calls),
        "called_tools": [call["tool_name"] for call in calls],
        "ok": all(call["ok"] for call in calls),
        "calls": calls,
    }

