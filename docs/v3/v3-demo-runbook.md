# MAGE-Doc V3 Demo Runbook

## 1. Demo 目标

用 5 到 8 分钟展示 V3 的核心价值：

> MAGE-Doc 不只会回答长文档问题，还能判断证据是否充分、诊断失败原因、选择 repair action，并用 benchmark report 证明自修复带来的可靠性提升。

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

## 3. 演示路径

1. 打开 Workbench，准备 demo document。
2. 在普通 Ask 面板提问 `What was revenue in 2026?`，展示 citation 和 claim verification。
3. 在 V3 Repair Trace 面板运行同一问题。
4. 展示 initial sufficiency、final sufficiency、diagnosis reason 和 selected repair action。
5. 解释 citation mismatch 如何触发 citation rerank 或 node type repair。
6. 打开 `eval/reports/v3_reliability_report.md`，展示 recovery rate、repair success rate、failure before/after。

## 4. 验证命令

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\app\tests
cd frontend
npm run build
```

生成 V3 reliability report：

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --cases eval\cases\v3_curated_cases.jsonl --output eval\reports\v3_reliability_report.json
```

## 5. 面试讲法

一句话：

> 我把长文档多模态 Agentic RAG 从“能回答”推进到“能自我诊断和自我修复”，通过 evidence sufficiency、failure taxonomy、repair policy 和 reliability benchmark 形成可观测的可靠性闭环。

重点展开：

- 为什么普通 RAG 难以保证可靠：错误通常混在 retrieval、citation、claim support、OCR/vision grounding 里。
- V3 如何拆解错误：taxonomy + sufficiency score。
- V3 如何修复错误：repair policy 将 failure reason 映射到 query rewrite、node type expansion、graph depth expansion、citation rerank。
- 如何证明有效：curated benchmark + before/after reliability report。

