from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.v2 import (
    FailureDiagnosisRequest,
    FailureDiagnosisResponse,
    McpCallRequest,
    McpCallResponse,
    McpSmokeResponse,
    McpToolResponse,
    V2StatusResponse,
)
from app.services.v2_failure_diagnosis import diagnose_results
from app.services.v2_mcp import call_mcp_tool, list_mcp_tools, run_mcp_smoke

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/status", response_model=V2StatusResponse)
def v2_status() -> V2StatusResponse:
    return {
        "version": settings.version,
        "batch": "Batch 3 - Advanced Multimodal Agent Platform",
        "status": "phase_5_8_complete",
        "capabilities": [
            {
                "name": "OCR Substrate",
                "phase": "V2 Phase 1",
                "status": "complete",
                "evidence": "ocr_text_block nodes and OCR run records",
            },
            {
                "name": "Vision Grounding",
                "phase": "V2 Phase 2",
                "status": "complete",
                "evidence": "chart and visual_summary evidence nodes",
            },
            {
                "name": "Metric Graph",
                "phase": "V2 Phase 3",
                "status": "complete",
                "evidence": "metric_value evidence nodes",
            },
            {
                "name": "Multi-Document Collection",
                "phase": "V2 Phase 4",
                "status": "complete",
                "evidence": "collection search with document metadata",
            },
            {
                "name": "MCP Tool Server",
                "phase": "V2 Phase 5",
                "status": "complete",
                "evidence": "MCP-compatible tool manifest and call endpoint",
            },
            {
                "name": "Benchmark Adapter",
                "phase": "V2 Phase 6",
                "status": "complete",
                "evidence": "benchmark JSONL import and submission export",
            },
            {
                "name": "Failure Diagnosis",
                "phase": "V2 Phase 7",
                "status": "complete",
                "evidence": "rule-based diagnosis distribution",
            },
            {
                "name": "V2 Release Polish",
                "phase": "V2 Phase 8",
                "status": "complete",
                "evidence": "runbook, README, workbench status panel",
            },
        ],
    }


@router.get("/mcp/tools", response_model=list[McpToolResponse])
def mcp_tools() -> list[McpToolResponse]:
    return list_mcp_tools()


@router.post("/mcp/call", response_model=McpCallResponse)
def mcp_call(payload: McpCallRequest, db: Session = Depends(get_db)) -> McpCallResponse:
    return call_mcp_tool(db, payload.name, payload.arguments)


@router.post("/mcp/smoke/{document_id}", response_model=McpSmokeResponse)
def mcp_smoke(document_id: str, db: Session = Depends(get_db)) -> McpSmokeResponse:
    return run_mcp_smoke(db, document_id)


@router.post("/failure-diagnosis", response_model=FailureDiagnosisResponse)
def failure_diagnosis(payload: FailureDiagnosisRequest) -> FailureDiagnosisResponse:
    return diagnose_results(payload.cases, payload.results)

