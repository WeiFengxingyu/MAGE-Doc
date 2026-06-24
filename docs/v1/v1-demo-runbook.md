# MAGE-Doc V1 Demo Runbook

## 1. Start Services

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

## 2. Prepare A Document

1. Open the frontend.
2. Upload a PDF.
3. Click `Prepare demo`.
4. Wait until the document status becomes `demo_ready`.

## 3. Hybrid Retrieval Demo

1. Search `Revenue 2026`.
2. Check result cards.
3. Explain the score breakdown:
   - lexical.
   - semantic.
   - metadata.
   - hybrid.

## 4. Agentic RAG Demo

1. Ask `What was revenue in 2026?`.
2. Show the answer.
3. Show citations.
4. Show trace id and tool trace.
5. Show claim verification status and claim-level reasons.
6. Click the citation and confirm the PDF bbox highlight.

## 5. Evaluation Demo

Run:

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v1_eval_report.json
```

Show:

- `eval/reports/v1_eval_report.json`
- `eval/reports/v1_eval_report.md`

## 6. Suggested Talking Points

- V0 proved the upload-parse-ask-cite-highlight loop.
- V1 adds evidence graph, graph expansion, trace persistence, claim verification, and evaluation.
- The system is intentionally local-first and deterministic before adding external LLM planners.
- Every answer can be connected back to citations, tool calls, and claim-level support status.
