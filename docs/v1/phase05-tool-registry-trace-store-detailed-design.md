# V1 Phase 5 详细设计：Tool Registry 与 Trace Store

## 1. Phase 目标

Phase 5 的目标是把 V0/V1 当前散落在响应里的 `tool_trace`，升级成可持久化、可查询、可审计的 Agent runtime 基础设施。

本阶段新增：

- Tool Registry：统一登记工具 schema、用途、输入字段和输出摘要策略。
- Trace Store：持久化 question run、planner step 和 tool call。
- Trace API：按 run id 查询完整执行轨迹。
- Agent 问答流程接入 trace store，同时保持原有响应兼容。

Phase 5 完成后，系统不再只是“返回一次 trace 数组”，而是可以在页面刷新后重新读取某次问答的执行过程。

## 2. 非目标

- 不引入 LLM planner。
- 不实现多 Agent 协作。
- 不把所有工具改成复杂插件系统。
- 不做 Phase 6 的 claim-level verification。
- 不新增复杂前端 trace timeline，本阶段只补类型和 API 能力。

## 3. 用户可见结果

用户调用问答 API 后：

- 响应中新增 `trace_id`。
- 原有 `trace` 数组继续存在。
- 可以通过 `GET /api/documents/{document_id}/traces/{trace_id}` 查询完整 trace。

开发者可以通过 Tool Registry 看到当前工具：

- `search_evidence`
- `inspect_page`
- `read_table`
- `verify_answer`
- `build_evidence_pack`

## 4. 数据模型

### 4.1 AgentTraceRun

表名：`agent_trace_runs`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid string | trace run id |
| `document_id` | string | 所属文档 |
| `question` | text | 用户问题 |
| `question_type` | string | `text_lookup` / `table_lookup` |
| `status` | string | `running` / `completed` / `failed` |
| `answer_preview` | text nullable | 答案摘要 |
| `metadata_json` | text | planner、策略、错误等 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 4.2 AgentToolCall

表名：`agent_tool_calls`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid string | tool call id |
| `trace_run_id` | string | 所属 trace run |
| `document_id` | string | 所属文档 |
| `step_index` | int | 调用顺序 |
| `tool_name` | string | 工具名 |
| `input_json` | text | 工具输入摘要 |
| `output_summary` | text | 输出摘要 |
| `latency_ms` | int | 耗时 |
| `status` | string | `completed` / `failed` |
| `metadata_json` | text | 错误、输出字段、候选数量等 |
| `created_at` | datetime | 创建时间 |

## 5. Tool Registry 设计

Registry 使用代码内静态注册，避免过早抽象。

每个工具定义：

| 字段 | 说明 |
| --- | --- |
| `name` | 工具名 |
| `description` | 工具作用 |
| `input_schema` | 输入字段说明 |
| `output_schema` | 输出字段说明 |
| `phase` | 引入阶段 |

Registry API：

```text
GET /api/tools
```

返回所有工具定义。

## 6. Trace API 设计

新增 API：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/api/tools` | 查询工具注册表 |
| `GET` | `/api/documents/{document_id}/traces` | 查询某文档 trace run 列表 |
| `GET` | `/api/documents/{document_id}/traces/{trace_id}` | 查询某次问答完整 trace |

## 7. Agent 接入策略

现有 `answer_question` 保持 deterministic flow：

```text
classify -> search_evidence -> read_table/inspect_page -> verify_answer
```

Phase 5 增量接入：

1. 创建 trace run。
2. 每次 `_append_trace` 时同步写入 `agent_tool_calls`。
3. 成功返回时标记 trace run `completed`。
4. 失败时标记 trace run `failed` 并记录错误。
5. 响应体新增 `trace_id`。

## 8. 兼容性

必须保持：

- `QuestionAnswerResponse.trace` 原结构不变。
- 原有 agent 测试只需新增对 `trace_id` 的断言，不破坏旧字段。
- retrieval、graph、evidence pack API 不强制写 trace store。

## 9. 测试策略

新增测试：

- `GET /api/tools` 返回已注册工具。
- 问答后响应包含 `trace_id`。
- trace run 可以通过 API 查询。
- trace detail 中 tool calls 顺序与响应 trace 一致。
- 空证据路径也能持久化 verify_answer tool call。

## 10. 验收标准

- `pytest backend/app/tests/test_trace_store.py` 通过。
- `pytest backend/app/tests/test_agent.py` 通过。
- 全量后端测试通过。
- 前端 build 通过。
- README、V1 计划、Batch 2 工作日志更新 Phase 5 状态。
- 本地 commit 并推送 GitHub。

## 11. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| trace store 和响应 trace 双写不一致 | 调试困难 | `_append_trace` 统一负责追加内存 trace 和写库 |
| tool registry 过早插件化 | 实现发散 | Phase 5 只做静态 registry |
| trace input/output 存太多内容 | SQLite 膨胀 | 只保存输入摘要和 output summary，完整大结果不入库 |
