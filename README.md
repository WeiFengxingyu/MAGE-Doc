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
- [V0 Phase 0 Detailed Design](docs/v0/phase00-project-skeleton-detailed-design.md)
- [V0 Phase 1 Detailed Design](docs/v0/phase01-document-upload-detailed-design.md)
- [V0 Phase 2 Detailed Design](docs/v0/phase02-page-rendering-coordinate-system-detailed-design.md)
- [V0 Phase 3 Detailed Design](docs/v0/phase03-text-block-parsing-detailed-design.md)
- [V0 Phase 4 Detailed Design](docs/v0/phase04-table-parsing-detailed-design.md)
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
