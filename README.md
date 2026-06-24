# MAGE-Doc

MAGE-Doc is a multimodal Agentic RAG system for long-PDF reasoning with evidence graphs.

The project focuses on high-value document intelligence scenarios where answers require text, tables, figures, page layout, section hierarchy, and cross-page evidence rather than plain top-k text retrieval.

## Positioning

**Chinese name:** MAGE-Doc：基于多模态证据图的长文档 Agentic RAG 系统

**English subtitle:** Multimodal Agentic RAG for Long-PDF Reasoning with Evidence Graphs

MAGE-Doc is designed as a resume-grade AI application project that is clearly different from a code-repository agent. It targets long annual reports, research reports, technical manuals, papers, prospectuses, and policy documents. The system parses PDFs into multimodal blocks, builds a page-section-block-table-figure evidence graph, and uses a tool-calling agent to retrieve, inspect, verify, and cite evidence.

## Documents

- [Requirements](docs/requirements.md)
- [Outline Design](docs/outline-design.md)
- [Development Plan](docs/development-plan.md)
- [Version Roadmap](docs/version-roadmap.md)
- [Batch 1 Implementation Plan](docs/batch1-implementation-plan.md)
- [Development Workflow](docs/development-workflow.md)
- [V1 Outline Design](docs/v1/v1-outline-design.md)
- [V1 Implementation Plan](docs/v1/v1-implementation-plan.md)
- [V1 Batch 2 Worklog](docs/v1/batch2-worklog.md)
- [V1 Phase 1 Detailed Design](docs/v1/phase01-evidence-graph-data-model-detailed-design.md)
- [V1 Phase 2 Detailed Design](docs/v1/phase02-layout-section-graph-detailed-design.md)
- [V1 Phase 3 Detailed Design](docs/v1/phase03-hybrid-retrieval-index-detailed-design.md)
- [V1 Phase 4 Detailed Design](docs/v1/phase04-graph-expansion-evidence-pack-detailed-design.md)
- [V1 Phase 5 Detailed Design](docs/v1/phase05-tool-registry-trace-store-detailed-design.md)
- [V1 Phase 6 Detailed Design](docs/v1/phase06-claim-verification-detailed-design.md)
- [V1 Phase 7 Detailed Design](docs/v1/phase07-evaluation-harness-detailed-design.md)
- [V1 Phase 8 Detailed Design](docs/v1/phase08-v1-workbench-polish-detailed-design.md)
- [V1 Demo Runbook](docs/v1/v1-demo-runbook.md)
- [V1 Evaluation Report](eval/reports/v1_eval_report.md)
- [V0 Phase 0 Detailed Design](docs/v0/phase00-project-skeleton-detailed-design.md)
- [V0 Phase 1 Detailed Design](docs/v0/phase01-document-upload-detailed-design.md)
- [V0 Phase 2 Detailed Design](docs/v0/phase02-page-rendering-coordinate-system-detailed-design.md)
- [V0 Phase 3 Detailed Design](docs/v0/phase03-text-block-parsing-detailed-design.md)
- [V0 Phase 4 Detailed Design](docs/v0/phase04-table-parsing-detailed-design.md)
- [V0 Phase 5 Detailed Design](docs/v0/phase05-retrieval-tools-detailed-design.md)
- [V0 Phase 6 Detailed Design](docs/v0/phase06-agentic-rag-loop-detailed-design.md)
- [V0 Phase 7 Detailed Design](docs/v0/phase07-qa-citation-highlight-detailed-design.md)
- [V0 Phase 8 Detailed Design](docs/v0/phase08-v0-demo-polish-detailed-design.md)
- [V0 Demo Runbook](docs/v0/v0-demo-runbook.md)
- [V0 Batch 1 Worklog](docs/v0/batch1-worklog.md)

## Quick Start

### Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Default backend URL:

- http://127.0.0.1:8000/health

### Frontend

```powershell
cd frontend
$env:npm_config_cache='F:\Desktop\agent\mage-doc\frontend\.npm-cache'
npm install
npm run dev
```

Default frontend URL:

- http://localhost:3000

## Phase 0 Status

Phase 0 project skeleton is complete:

- FastAPI backend skeleton with `/health` and `/api/status`.
- Next.js workbench shell with backend status panel.
- Docker Compose skeleton.
- Backend health tests.
- Frontend production build.

## Phase 1 Status

Phase 1 document upload and status management is complete:

- Standard multipart PDF upload API.
- SQLite-backed document metadata model.
- Original PDF storage under `.magedoc/uploads/<document_id>/original.pdf`.
- Document list, detail, and status APIs.
- Frontend upload form and document list.
- Backend document API tests.
- Frontend production build.

## Phase 2 Status

Phase 2 page rendering and coordinate system is complete:

- PyMuPDF-based PDF page rendering.
- `pages` metadata model with PDF point size and PNG pixel size.
- Render API, page list/detail APIs, and page image API.
- Document `page_count` and `status=rendered` update after rendering.
- Frontend render action, page viewer, image display, and test bbox overlay.
- Backend page rendering tests.
- Visual smoke check against a generated PDF page PNG.

## Phase 3 Status

Phase 3 text block parsing and evidence nodes is complete:

- PyMuPDF-based text block extraction from rendered PDFs.
- Unified `evidence_nodes` model for `text_block` nodes.
- Text content, page binding, bbox, reading order, and parser metadata persistence.
- Text parsing API, document text-block list API, and page text-block list API.
- Document `status=parsed` update after successful parsing.
- Frontend `Parse text` action and real text bbox overlay on the page viewer.
- Backend evidence parsing tests.
- End-to-end smoke check across upload, render, parse, and bbox response.

## Phase 4 Status

Phase 4 basic table parsing and table evidence nodes is complete:

- PyMuPDF `page.find_tables()` based table detection.
- Unified `evidence_nodes` model extended with `node_type=table`.
- Table bbox, cell bbox, row/column count, matrix, and TSV text persistence.
- Table parsing API, document table list API, and page table list API.
- Document `status=tables_parsed` update after successful table parsing.
- Frontend `Parse tables` action and table bbox overlay on the page viewer.
- Backend table parsing tests with generated ruled-table PDFs.
- End-to-end smoke check across upload, render, parse tables, and matrix response.

## Phase 5 Status

Phase 5 basic retrieval and tool layer is complete:

- Local BM25-style retrieval over `text_block` and `table` evidence nodes.
- Tool-shaped backend functions for `search_evidence`, `inspect_page`, `read_table`, and `verify_answer`.
- Search responses include score, matched terms, snippet, page, bbox, node id, and tool trace.
- Page inspection API and table reading API for future Agent workflows.
- Basic citation verification API.
- Frontend retrieval panel with scope selection and evidence result cards.
- Backend retrieval tests with generated text/table PDFs.
- End-to-end smoke check across upload, render, parse, search, and trace response.

## Phase 6 Status

Phase 6 V0 Agentic RAG loop is complete:

- Deterministic local workflow agent over the Phase 5 tool layer.
- Lightweight question classification for table lookup and text lookup.
- Tool plans for `search_evidence -> read_table -> verify_answer` and `search_evidence -> inspect_page -> verify_answer`.
- Answer responses with citations, page numbers, bbox, node ids, trace, and verification.
- Question API at `POST /api/documents/{document_id}/questions`.
- Frontend Ask panel with answer, citation, trace, and verification display.
- Backend agent tests with generated text/table PDFs.
- End-to-end smoke check across upload, render, parse, ask, cite, trace, and verify.

## Phase 7 Status

Phase 7 frontend QA citation highlighting is complete:

- Client-side document workbench for shared citation selection state.
- Ask panel citations are clickable and show active selection styling.
- Page viewer switches to the selected citation page.
- Selected citation bbox is highlighted over the rendered PDF page.
- Page viewer keeps text and table overlays while adding citation highlight.
- Frontend build validates the interaction wiring.
- Backend regression tests remain green.

## Phase 8 Status

Phase 8 V0 demo polish and one-click preparation is complete:

- Prepare-demo pipeline API runs page rendering, text parsing, and table parsing in one request.
- Document status supports `preparing_demo` and `demo_ready`.
- Frontend document cards include a primary `Prepare demo` action.
- Demo-ready documents show a guided workbench notice.
- V0 demo runbook documents the full upload, prepare, ask, cite, and highlight flow.
- Backend pipeline tests verify prepare-demo and follow-up question answering.
- End-to-end smoke check confirms prepare-demo reaches `demo_ready` and questions return verified citations.

## V1 Phase 1-8 Status

V1 Phase 1-8 evidence graph, hybrid retrieval, evidence pack, trace runtime, claim verification, evaluation, and workbench polish is complete:

- Evidence graph edge model and graph APIs for build, summary, and node neighbors.
- Layout graph enrichment with section, table cell, caption, and near relations.
- Hybrid retrieval results with lexical, semantic fallback, metadata score breakdown, and candidate sources.
- Evidence Pack API expands hybrid candidates through graph relations into answer-ready context.
- Tool Registry documents available Agent tools and Trace Store persists question runs and tool calls.
- Claim Verification splits answers into verifiable claims and labels supported, partial, unsupported, or insufficient evidence.
- Evaluation harness compares V0 agent baseline and V1 evidence pack strategy on local synthetic long-document cases.
- Workbench shows hybrid score breakdown, trace id, citation coverage, and claim verification details.
- Backend graph, retrieval, evidence pack, agent, trace, claim verification, and eval tests validate the V1 foundation while preserving the V0 flow.

Run V1 evaluation:

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v1_eval_report.json
```
