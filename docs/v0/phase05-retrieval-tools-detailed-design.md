# Phase 5 Detailed Design: 基础检索与工具层

## 1. Phase 目标

Phase 5 在 Phase 3/4 已落库的 `text_block` 和 `table` evidence nodes 上建立基础检索与工具层。目标不是直接生成答案，而是为 Phase 6 的 Agentic RAG 提供可调用、可测试、可追踪的工具边界。

核心闭环：

```text
query -> search_evidence -> inspect_page/read_table -> verify_answer
```

本阶段必须让文本块和表格都能被召回，并且每个召回结果都保留 `document_id`、`page_number`、`bbox`、`node_id` 和分数解释。

## 2. 非目标

- 不接入外部 embedding 服务。
- 不做 LLM 答案生成。
- 不做多轮 Agent planning。
- 不做跨文档检索。
- 不做持久化倒排索引。
- 不做复杂 query rewriting。

## 3. 用户可见结果

- 用户可以在前端输入检索 query。
- 系统返回相关文本块和表格 evidence。
- 结果展示 page、node type、score、bbox、文本摘要。
- 系统提供基础工具接口，后续 Agent 可直接调用。

## 4. 工具选型

### 4.1 V0 主检索：本地 BM25-style keyword retrieval

Phase 5 使用无外部依赖的 BM25-style 检索。

选择原因：

- 本地可运行，不依赖模型 key、向量库或网络。
- 对 V0 的文本块、表格摘要、指标名检索足够可测。
- 分数可解释，方便 debug 和工具 trace。
- 后续可替换为 hybrid retrieval，不影响工具 API 形状。

### 4.2 后续增强

- Embedding + reranker：V1 接入语义召回和重排。
- Evidence graph expansion：基于 page/table/nearby relation 扩展上下文。
- Query planner：Phase 6 由 Agent 决定调用 search/read/verify。

## 5. 后端服务设计

新增 `backend/app/services/retrieval.py`。

核心函数：

- `search_evidence(db, document_id, query, node_types=None, top_k=5)`
  - 从 `evidence_nodes` 读取 `text_block` 和 `table`。
  - 对 query 和 evidence text/metadata 文本做 tokenization。
  - 使用 BM25-style scoring 计算分数。
  - 返回 top-k evidence result。
- `inspect_page_tool(db, document_id, page_number)`
  - 返回页面元数据和该页 evidence 概览。
- `read_table_tool(db, document_id, table_id)`
  - 读取 table evidence node。
  - 返回 bbox、matrix、cells、row_count、col_count。
- `verify_answer_tool(db, document_id, answer, citation_node_ids)`
  - 基础规则校验：citation 是否存在、是否属于该文档、answer 是否为空。
  - 返回 passed、missing citations、covered citations。

## 6. API 设计

新增接口：

```text
GET  /api/documents/{document_id}/search?query=...&top_k=5&node_types=text_block,table
GET  /api/documents/{document_id}/tools/inspect-page/{page_number}
GET  /api/documents/{document_id}/tools/read-table/{table_id}
POST /api/documents/{document_id}/tools/verify-answer
```

### 6.1 Search response

```json
{
  "query": "revenue 2026",
  "document_id": "uuid",
  "results": [
    {
      "node": { "...EvidenceNodeResponse": "..." },
      "score": 3.42,
      "matched_terms": ["revenue", "2026"],
      "snippet": "Revenue 100 128",
      "rank": 1
    }
  ],
  "tool_trace": {
    "tool_name": "search_evidence",
    "input": { "query": "revenue 2026", "top_k": 5 },
    "output_summary": "1 results",
    "latency_ms": 2
  }
}
```

### 6.2 Verify request

```json
{
  "answer": "Revenue increased to 128 in 2026.",
  "citation_node_ids": ["node-id"]
}
```

## 7. Schema 设计

新增 `backend/app/schemas/tools.py`：

- `SearchResultResponse`
- `SearchResponse`
- `InspectPageResponse`
- `ReadTableResponse`
- `VerifyAnswerRequest`
- `VerifyAnswerResponse`
- `ToolTraceResponse`

设计原则：

- 工具响应显式携带 trace，方便 Phase 6 复用。
- 搜索结果内嵌 EvidenceNodeResponse，保证 citation 信息完整。
- `read_table` 不只返回文本摘要，还返回 matrix 和 cell bbox。

## 8. 前端交互设计

新增 `RetrievalPanel`：

- 绑定当前 active document。
- 输入 query。
- 选择 scope：
  - All evidence
  - Text only
  - Tables only
- 提交后显示 search results。
- 每条结果显示：
  - rank、node type、page、score。
  - snippet。
  - matched terms。
  - bbox。

前端暂不做点击结果跳转高亮。Phase 7 再将检索结果和页面 viewer 的高亮状态联动。

## 9. 测试和验收标准

后端测试：

- 生成含文本和表格的 PDF。
- 上传、渲染、解析文本、解析表格。
- `search` 能用关键词召回文本块。
- `search` 能用指标名召回表格。
- `inspect_page` 返回页面和 evidence 概览。
- `read_table` 返回 matrix 和 cell bbox。
- `verify_answer` 对存在/缺失 citation 给出正确结果。

前端验证：

- TypeScript 类型通过。
- `npm run build` 通过。
- `RetrievalPanel` 能渲染空状态、未选择文档状态和结果状态。

Smoke：

- 生成测试 PDF。
- 完成 upload/render/parse/search。
- 输出 top result node type、page、matched_terms、score。

## 10. 风险和取舍

- BM25-style 检索不具备语义泛化能力，但便于本地闭环和可解释 debug。
- 不持久化索引会让大文档检索变慢，V0 可接受；后续再引入索引表或向量库。
- 中文分词先采用字符 bigram + ASCII token 混合策略，避免引入额外依赖。
- 工具 trace 先随响应返回，不写入数据库；Phase 6/7 再设计持久化 trace。

## 11. 完成定义

- Phase 5 详细设计完成。
- 后端 retrieval service、schemas、API、测试完成。
- 前端检索调试面板完成。
- 后端测试通过。
- 前端构建通过。
- 检索 smoke 通过。
- README 和 Batch 1 工作日志更新。
- 提交并推送 GitHub。
