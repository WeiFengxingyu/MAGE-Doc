# MAGE-Doc V1 Batch 2 工作日志

## 2026-06-24：V1 规划启动

### 当前阶段

Batch 2 - Evidence Graph Agentic RAG planning。

### 用户要求

- V0 已经闭环后，开始专心推进新项目的 V1。
- V1 继续使用 V0 的开发工作流：每个小 Phase 先写详细设计，再实现，再验证，再记录工作日志。
- 本次先写 V1 的概要设计和分阶段计划文档，不直接进入代码实现。

### 关键决策

- V1 不做“普通 PDF RAG 功能堆叠”，而是围绕 evidence graph、hybrid retrieval、graph expansion、agent tool trace、claim verification 和 evaluation 加深。
- V1 作为 Batch 2，不替换 V0，而是在 V0 上传、渲染、解析、问答和引用高亮闭环之上继续演进。
- V1 仍采用本地优先技术路线：FastAPI、SQLite、PyMuPDF、Next.js，外部 embedding 或 LLM 只作为 adapter。
- Agent runtime 先保持 deterministic，优先保证可测、可复现、可追踪，再为后续 LLM planner 留扩展点。

### 本次产出

- `docs/v1/v1-outline-design.md`：V1 概要设计。
- `docs/v1/v1-implementation-plan.md`：V1 分阶段实现计划。
- `docs/v1/batch2-worklog.md`：V1 大阶段工作日志。

### V1 Phase 初始划分

| Phase | 名称 | 状态 |
| --- | --- | --- |
| Phase 1 | Evidence Graph 数据模型 | 已完成 |
| Phase 2 | Layout 关系与 Section 构建 | 已完成 |
| Phase 3 | Hybrid Retrieval Index | 已完成 |
| Phase 4 | Graph Expansion 与 Evidence Pack | 已完成 |
| Phase 5 | Tool Registry 与 Trace Store | 已完成 |
| Phase 6 | Claim Verification | 已完成 |
| Phase 7 | Evaluation Harness | 待开始 |
| Phase 8 | V1 Workbench Polish | 待开始 |

### 下一步

进入 V1 Phase 1：

1. 新建 `docs/v1/phase01-evidence-graph-data-model-detailed-design.md`。
2. 明确 edge table、graph service、graph build API 和测试策略。
3. 根据详细设计实现数据模型和基础图构建。
4. 验证 graph build、neighbor query 和幂等构建。

## 2026-06-24：Phase 1-3 闭环

### 当前阶段

V1 Phase 1 到 Phase 3 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### Phase 1：Evidence Graph 数据模型

产出：

- 新增 `EvidenceEdge` 模型。
- 新增 graph service，支持 graph build、graph summary 和 node neighbors。
- 新增 graph API：
  - `POST /api/documents/{document_id}/graph/build`
  - `GET /api/documents/{document_id}/graph`
  - `GET /api/documents/{document_id}/graph/neighbors/{node_id}`
- 新增 graph 单测，覆盖幂等构图、contains/next 边和邻域查询。

### Phase 2：Layout 关系与 Section 构建

产出：

- graph build 自动生成 `section`、`table_cell`、`caption` 节点。
- 新增 `part_of`、`caption_of`、`near` 和 section `contains` 边。
- 使用可解释 heuristic 识别标题、caption candidate、同页邻近节点。
- graph API 可返回 V1 的 layout graph enrichment 结果。

### Phase 3：Hybrid Retrieval Index

产出：

- `search_evidence` 从 V0 lexical 检索升级为 hybrid scoring。
- 新增 semantic fallback adapter，使用本地 hash-vector cosine，不依赖外部 API。
- 新增 metadata score，对 table/table_cell/caption/section 等节点类型提供结构化信号。
- Search result 新增 `retrieval_source`、`candidate_sources` 和 `score_breakdown`。
- 原有 search response 保持向后兼容。
- 前端 API 类型同步支持 `section`、`table_cell`、`caption` 节点和 hybrid search 解释字段。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_graph.py`：通过。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_retrieval.py`：通过。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：27 passed，1 warning。
- `npm run build`：Next.js production build 通过。
- 类型同步后复验 `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_graph.py backend\app\tests\test_retrieval.py`：6 passed，1 warning。
- 类型同步后复验 `npm run build`：通过。

### 下一步

进入 V1 Phase 4：Graph Expansion 与 Evidence Pack。

Phase 4 必须先写 `docs/v1/phase04-graph-expansion-evidence-pack-detailed-design.md`，再实现从 hybrid candidates 到 answer-ready evidence pack 的图邻域扩展。

## 2026-06-24：Phase 4 闭环

### 当前阶段

V1 Phase 4 - Graph Expansion 与 Evidence Pack 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### 详细设计

- 新增 `docs/v1/phase04-graph-expansion-evidence-pack-detailed-design.md`。
- 明确 evidence pack 输入输出、graph expansion 策略、inclusion reason、排序规则和验收标准。

### 实现摘要

- 新增 `backend/app/schemas/evidence_pack.py`。
- 新增 `backend/app/services/evidence_pack.py`。
- 新增 API：`GET /api/documents/{document_id}/evidence-pack`。
- Evidence Pack 会先调用 hybrid retrieval，再按 `contains`、`next`、`part_of`、`caption_of`、`near` 扩展图邻域。
- 每个 pack item 记录：
  - source candidate id。
  - source candidate rank。
  - graph distance。
  - inclusion reason。
  - edge path。
  - score breakdown。
- 前端 API 类型新增 `EvidenceEdge`、`EvidencePackItem`、`EvidencePackResponse`。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_evidence_pack.py`：2 passed，1 warning。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：29 passed，1 warning。
- `npm run build`：Next.js production build 通过。

### 下一步

进入 V1 Phase 5：Tool Registry 与 Trace Store。

Phase 5 必须先写 `docs/v1/phase05-tool-registry-trace-store-detailed-design.md`，再把工具 schema、tool call 持久化和 trace API 做成 Agent runtime 的基础设施。

## 2026-06-24：Phase 5 闭环

### 当前阶段

V1 Phase 5 - Tool Registry 与 Trace Store 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### 详细设计

- 新增 `docs/v1/phase05-tool-registry-trace-store-detailed-design.md`。
- 明确工具注册表、trace run、tool call、trace 查询 API 和 Agent 接入策略。

### 实现摘要

- 新增 `AgentTraceRun` 和 `AgentToolCall` 数据模型。
- 新增 `backend/app/services/tool_registry.py`，静态注册当前 Agent 工具：
  - `search_evidence`
  - `inspect_page`
  - `read_table`
  - `verify_answer`
  - `build_evidence_pack`
- 新增 `backend/app/services/trace_store.py`，支持 trace run 创建、tool call 记录、完成/失败状态更新、列表和详情查询。
- 新增 `GET /api/tools`。
- 新增 trace API：
  - `GET /api/documents/{document_id}/traces`
  - `GET /api/documents/{document_id}/traces/{trace_id}`
- `POST /api/documents/{document_id}/questions` 响应新增 `trace_id`，原有 `trace` 数组保持兼容。
- 每次 deterministic Agent 调用工具时同步持久化 tool call。
- 前端 API 类型新增 Tool Registry 和 Trace Store 相关类型。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_trace_store.py backend\app\tests\test_agent.py`：7 passed，1 warning。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：32 passed，1 warning。
- `npm run build`：Next.js production build 通过。

### 下一步

进入 V1 Phase 6：Claim Verification。

Phase 6 必须先写 `docs/v1/phase06-claim-verification-detailed-design.md`，再把答案拆解为 claims，并基于 evidence pack、citation 和 trace 输出 supported / partial / unsupported。

## 2026-06-24：Phase 6 闭环

### 当前阶段

V1 Phase 6 - Claim Verification 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### 详细设计

- 新增 `docs/v1/phase06-claim-verification-detailed-design.md`。
- 明确 claim 状态、claim extraction、evidence binding、verification 规则、Agent 响应和 Trace Store 接入策略。

### 实现摘要

- 新增 `backend/app/schemas/claim_verification.py`。
- 新增 `backend/app/services/claim_verification.py`。
- `POST /api/documents/{document_id}/questions` 响应新增 `claim_verification`。
- Agent trace 新增 `verify_claims` tool call。
- Trace Run metadata 新增：
  - `claim_verification_status`
  - `claim_count`
  - `unsupported_count`
- Tool Registry 新增 `verify_claims`。
- 前端 API 类型新增 `ClaimVerification` 和 `ClaimVerificationItem`。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_claim_verification.py`：3 passed，1 warning。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_claim_verification.py backend\app\tests\test_agent.py backend\app\tests\test_trace_store.py`：10 passed，1 warning。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：35 passed，1 warning。
- `npm run build`：Next.js production build 通过。

### 下一步

进入 V1 Phase 7：Evaluation Harness。

Phase 7 必须先写 `docs/v1/phase07-evaluation-harness-detailed-design.md`，再建立小型公开 PDF QA 数据集、策略 runner 和指标报告。
