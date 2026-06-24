from typing import Any


TOOL_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "search_evidence",
        "description": "Hybrid retrieval over parsed evidence nodes.",
        "input_schema": {"query": "string", "top_k": "integer", "node_types": "string|null"},
        "output_schema": {"results": "array", "tool_trace": "object"},
        "phase": "V0 Phase 5 / V1 Phase 3",
    },
    {
        "name": "inspect_page",
        "description": "Inspect page metadata and evidence node summaries.",
        "input_schema": {"page_number": "integer"},
        "output_schema": {"page_number": "integer", "evidence": "array", "tool_trace": "object"},
        "phase": "V0 Phase 5",
    },
    {
        "name": "read_table",
        "description": "Read a structured table evidence node.",
        "input_schema": {"table_id": "string"},
        "output_schema": {"matrix": "array", "cells": "array", "tool_trace": "object"},
        "phase": "V0 Phase 5",
    },
    {
        "name": "verify_answer",
        "description": "Verify answer presence and citation node coverage.",
        "input_schema": {"answer": "string", "citation_node_ids": "array"},
        "output_schema": {"passed": "boolean", "covered_citation_node_ids": "array"},
        "phase": "V0 Phase 5",
    },
    {
        "name": "build_evidence_pack",
        "description": "Expand hybrid retrieval candidates through evidence graph relations.",
        "input_schema": {
            "query": "string",
            "top_k": "integer",
            "depth": "integer",
            "edge_types": "string|null",
        },
        "output_schema": {"items": "array", "summary": "object", "tool_trace": "object"},
        "phase": "V1 Phase 4",
    },
]


def list_registered_tools() -> list[dict[str, Any]]:
    return TOOL_REGISTRY
