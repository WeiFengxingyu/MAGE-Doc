# Phase 6 Detailed Design: V0 Agentic RAG 闭环

## 1. Phase 目标

Phase 6 在 Phase 5 工具层之上完成 V0 Agentic RAG 最小闭环。系统接收用户问题，进行轻量分类和计划，调用检索/读表/页面检查/引用校验工具，生成带 citation 的可解释答案，并返回完整 tool trace。

本阶段重点不是答案文采，而是证明：

```text
question -> classify -> plan -> tool calls -> answer -> citations -> verify
```

## 2. 非目标

- 不调用外部 LLM API。
- 不做复杂多轮规划。
- 不做自然语言生成优化。
- 不做引用点击高亮联动。
- 不持久化 question 和 tool_calls。
- 不做跨文档问答。

## 3. 用户可见结果

- 用户可以在前端 Ask 面板输入问题。
- 后端返回答案、引用证据和工具调用 trace。
- 表格型问题优先检索/读取表格证据。
- 文本型问题优先检索文本证据。
- 答案引用包含 page、bbox、node_id、node_type。
- verify 工具会检查引用是否存在并返回校验状态。

## 4. Agent 设计

### 4.1 V0 Agent 类型

Phase 6 使用确定性 workflow agent。

原因：

- 本地可运行，不依赖模型 key。
- 每一步可测试、可解释。
- 工具边界能直接迁移到后续 LLM/LangGraph agent。
- 避免在 V0 被模型不稳定性卡住。

### 4.2 Query classification

规则分类：

- `table_lookup`
  - 命中 revenue、margin、metric、2025、2026、费用、收入、利润、表格、指标等。
  - 优先搜索 `table`。
- `text_lookup`
  - 默认类型。
  - 优先搜索 `text_block`。

### 4.3 Tool plan

表格型问题：

```text
search_evidence(node_types=table)
read_table(top table)
verify_answer(citation_node_ids=[top table])
```

文本型问题：

```text
search_evidence(node_types=text_block)
inspect_page(top page)
verify_answer(citation_node_ids=[top text block])
```

如果首轮没有结果，则 fallback 到 all evidence 搜索。

## 5. 后端服务设计

新增 `backend/app/services/agent.py`。

核心函数：

- `answer_question(db, document_id, question)`
  - 校验问题非空。
  - 分类问题。
  - 生成工具计划。
  - 调用 Phase 5 工具。
  - 从 top evidence 合成模板答案。
  - 生成 citations。
  - 调用 verify answer。
  - 返回 answer、citations、trace、verification。

答案生成策略：

- 表格答案：
  - 从 `read_table` matrix 中选择包含 query term 的行。
  - 输出 “Based on table evidence on page X...”。
- 文本答案：
  - 使用 top evidence snippet 作为 grounded answer。
  - 输出 “Based on text evidence on page X...”。
- 无结果：
  - 输出无法找到证据，并返回空 citations。

## 6. API 设计

新增接口：

```text
POST /api/documents/{document_id}/questions
```

请求：

```json
{
  "question": "What was revenue in 2026?"
}
```

响应：

```json
{
  "document_id": "uuid",
  "question": "What was revenue in 2026?",
  "question_type": "table_lookup",
  "answer": "Based on table evidence on page 1...",
  "citations": [
    {
      "node_id": "uuid",
      "node_type": "table",
      "page_number": 1,
      "bbox": [60.0, 95.0, 330.0, 179.0],
      "snippet": "Revenue 100 128"
    }
  ],
  "trace": [
    {
      "tool_name": "search_evidence",
      "input": {},
      "output_summary": "1 results",
      "latency_ms": 3
    }
  ],
  "verification": {
    "passed": true
  }
}
```

## 7. Schema 设计

新增到 `backend/app/schemas/agent.py`：

- `QuestionRequest`
- `CitationResponse`
- `QuestionAnswerResponse`

复用 Phase 5：

- `ToolTraceResponse`
- `VerifyAnswerResponse`

## 8. 前端交互设计

新增 `AskPanel`：

- 绑定当前 active document。
- 输入 question。
- 提交后展示：
  - answer。
  - citations。
  - trace。
  - verification 状态。

本阶段不做 citation 点击跳转和页面高亮联动，留到 Phase 7。

## 9. 测试和验收标准

后端测试：

- 生成含正文和表格的 PDF。
- 上传、渲染、解析文本、解析表格。
- 表格问题返回 table citation，并调用 `read_table` 和 `verify_answer`。
- 文本问题返回 text citation，并调用 `inspect_page` 和 `verify_answer`。
- 空问题返回 400。
- 无结果问题返回空 citations，verification 不通过。

前端验证：

- TypeScript 类型通过。
- `npm run build` 通过。
- Ask 面板能显示 answer/citations/trace。

Smoke：

- 生成测试 PDF。
- 完成 upload/render/parse/question。
- 输出 answer、question_type、citation count、trace tool names、verification passed。

## 10. 风险和取舍

- V0 使用模板答案，不具备 LLM 的语言泛化能力。
- 问题分类是规则型，边界问题可能误分类。
- 表格行选择是轻量启发式，不保证复杂财报指标解析。
- 但工具链、citation、verification 形状已经稳定，可平滑升级到 LLM planner/generator。

## 11. 完成定义

- Phase 6 详细设计完成。
- 后端 agent service、schema、API、测试完成。
- 前端 Ask 面板完成。
- 后端测试通过。
- 前端构建通过。
- Agent smoke 通过。
- README 和 Batch 1 工作日志更新。
