# V2 Phase 5 详细设计：MCP Tool Server

## 1. 目标

Phase 5 的目标是把 MAGE-Doc 的核心文档智能能力暴露成外部 Agent 可调用的工具层。它不依赖外部 MCP runtime，也不改变 FastAPI 主服务，而是在项目内实现一个 MCP-compatible adapter：

- 提供稳定 tool manifest。
- 支持统一 `call_tool` 分发。
- 工具输出复用内部 service，保证与 API 行为一致。
- 提供本地 smoke，证明至少 3 个工具可被外部 Agent 调用。

## 2. 工具范围

Phase 5 最小工具集：

| Tool | 输入 | 输出 | 内部能力 |
| --- | --- | --- | --- |
| `search_doc` | `document_id`, `query`, `top_k`, `node_types` | hybrid candidates | `search_evidence` |
| `inspect_page` | `document_id`, `page_number` | page metadata + evidence summaries | `inspect_page_tool` |
| `read_table` | `document_id`, `table_id` | table matrix + cells | `read_table_tool` |
| `build_evidence_pack` | `document_id`, `query`, `top_k`, `depth`, `node_types`, `edge_types` | graph-expanded evidence pack | `build_evidence_pack` |
| `verify_claims` | `document_id`, `answer`, `citations`, `question_type` | claim verification result | `verify_claims` |

## 3. 接口设计

新增 service：

```text
backend/app/services/v2_mcp.py
```

核心函数：

- `list_mcp_tools() -> list[dict]`
- `call_mcp_tool(db, name, arguments) -> dict`
- `run_mcp_smoke(db, document_id) -> dict`

新增 API：

```text
GET  /api/v2/mcp/tools
POST /api/v2/mcp/call
POST /api/v2/mcp/smoke/{document_id}
```

`call` 请求：

```json
{
  "name": "search_doc",
  "arguments": {
    "document_id": "...",
    "query": "revenue",
    "top_k": 3
  }
}
```

`call` 响应采用 MCP-style envelope：

```json
{
  "tool_name": "search_doc",
  "ok": true,
  "content": [{"type": "json", "json": {}}],
  "tool_trace": {}
}
```

## 4. 错误处理

- 未知工具返回 404。
- 缺少必填参数返回 400。
- 内部 service 的 404 继续透传。
- 工具异常不吞掉，测试中保持可见。

## 5. 验收

- `/api/v2/mcp/tools` 至少返回 5 个工具。
- `call_tool` 能调用 `search_doc`、`inspect_page`、`build_evidence_pack`。
- smoke client 能在一个已准备文档上调用至少 3 个工具。
- 工具结果和内部 API 使用同一 service 输出。

