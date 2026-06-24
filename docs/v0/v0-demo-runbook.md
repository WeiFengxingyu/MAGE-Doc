# MAGE-Doc V0 Demo Runbook

## Goal

Run the complete V0 demo:

```text
Upload PDF -> Prepare demo -> Ask -> Click citation -> Highlight evidence bbox
```

## 1. Start Backend

```powershell
cd F:\Desktop\agent\mage-doc\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Backend URL:

- http://127.0.0.1:8000/health

## 2. Start Frontend

```powershell
cd F:\Desktop\agent\mage-doc\frontend
$env:npm_config_cache='F:\Desktop\agent\mage-doc\frontend\.npm-cache'
npm run dev
```

Frontend URL:

- http://localhost:3000

## 3. Upload a PDF

Use the upload form in the document workspace.

For the strongest V0 demo, use a PDF that contains:

- normal embedded text
- at least one ruled table
- a short financial or metric-like question target

## 4. Prepare Demo

Click `Prepare demo` on the uploaded document card.

This runs:

1. page rendering
2. text block parsing
3. table parsing

When complete, the document status becomes `demo_ready`.

## 5. Ask a Question

Use the Ask panel.

Example:

```text
What was revenue in 2026?
```

Expected result:

- answer is generated
- citation list is shown
- trace includes search/read/verify tools
- verification is passed when citation exists

## 6. Click Citation

Click a citation card in the Ask panel.

Expected result:

- page viewer switches to the cited page
- cited bbox is highlighted in amber
- text/table overlays remain visible

## 7. Demo Talking Points

- Evidence nodes preserve `page`, `bbox`, `node_id`, and `node_type`.
- The Agent does not answer from memory; it calls retrieval/read/verify tools.
- Citations are inspectable and visually grounded on the rendered PDF page.
- V0 is local and deterministic, ready for V1 upgrades with embeddings, reranking, and LLM planning.
