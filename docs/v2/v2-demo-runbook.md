# MAGE-Doc V2 Demo Runbook

## 1. Demo 目标

用 5 到 8 分钟展示 MAGE-Doc 从 V0/V1 的长文档 Agentic RAG，升级为 V2 Advanced Multimodal Agent Platform：

- OCR substrate 支持扫描页证据。
- Vision grounding 支持图表和视觉摘要证据。
- Metric graph 支持结构化数值 reasoning。
- Collection 支持跨文档检索。
- MCP-compatible tools 支持外部 Agent 调用。
- Benchmark adapter 和 failure diagnosis 支持可评测、可诊断闭环。

## 2. 启动

Backend：

```powershell
cd F:\Desktop\agent\mage-doc
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Frontend：

```powershell
cd F:\Desktop\agent\mage-doc\frontend
npm run dev
```

## 3. 演示顺序

1. 打开 workbench，说明 V2 capability panel 中 8 个 phase 均为 complete。
2. 上传或使用 synthetic PDF，点击 prepare demo。
3. 提问 `What was revenue in 2026?`，展示答案、citation、bbox highlight 和 trace。
4. 调用 OCR、vision grounding、metric graph API，说明扫描页、图表和指标节点都会进入 evidence graph。
5. 打开 `/api/v2/mcp/tools`，展示外部 Agent 可调用工具 manifest。
6. 对同一 document 调用 `/api/v2/mcp/smoke/{document_id}`，展示 `search_doc`、`inspect_page`、`build_evidence_pack` 三个工具调用成功。
7. 运行 V2 benchmark report，展示 `v2_multimodal_graph` strategy 和 failure diagnosis distribution。

## 4. 验证命令

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\app\tests
cd frontend
npm run build
```

生成 V2 benchmark report：

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v2_benchmark_report.json
```

## 5. 面试讲法

一句话：

> MAGE-Doc 是一个面向长 PDF 的多模态 Agentic RAG 系统，我把文档解析成 text/table/OCR/chart/metric evidence graph，并通过工具调用、MCP adapter、benchmark adapter 和 failure diagnosis 做到可引用、可验证、可评测。

重点展开：

- 为什么不是普通 RAG：检索对象不是 chunk，而是带 bbox、page、node type、graph edge 的 evidence node。
- 为什么 Agentic：回答链路会调用 search、inspect page、read table、evidence pack、verify claims 等工具。
- 为什么前沿：V2 支持 OCR、vision grounding、metric graph、多文档 collection、MCP tool server、benchmark adapter 和 failure diagnosis。

