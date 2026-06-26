# MAGE-Doc V3 Batch 4 工作日志

## 2026-06-26：V3 规划启动

### 当前阶段

Batch 4 - Failure-Aware Self-Correcting Agentic RAG planning。

### 用户要求

- 基于当前项目现状继续深化。
- 先写 V3 概要设计和计划文档。
- V3 要比 V2 更有深度，更适合简历和面试讲解。

### 当前基线

V2 已完成：

- OCR Substrate。
- Vision Grounding。
- Metric Graph。
- Multi-Document Collection。
- MCP-compatible Tool Server。
- Benchmark Adapter。
- Failure Diagnosis。
- V2 Release Polish。

### V3 关键决策

- V3 不继续横向堆功能，而是围绕 reliable Agentic RAG 深化。
- 将 V2 的 failure diagnosis 变成可执行 repair signal。
- 将 Agent 从固定工具链升级为 diagnose-repair-verify 的自修复循环。
- 用 benchmark-driven reliability report 证明修复前后提升。
- 保持本地可运行和可测试，不强依赖外部模型。

### 本次产出

- `docs/v3/v3-outline-design.md`：V3 概要设计。
- `docs/v3/v3-implementation-plan.md`：V3 分阶段实现计划。
- `docs/v3/batch4-worklog.md`：V3 大阶段工作日志。

### V3 Phase 初始划分

| Phase | 名称 | 状态 |
| --- | --- | --- |
| Phase 1 | Failure Taxonomy 2.0 | 已完成 |
| Phase 2 | Evidence Sufficiency Scoring | 已完成 |
| Phase 3 | Repair Policy Engine | 已完成 |
| Phase 4 | Self-Correcting Agent Loop | 已完成 |
| Phase 5 | Curated Benchmark Suite | 已完成 |
| Phase 6 | Reliability Evaluation | 已完成 |
| Phase 7 | Workbench Repair Trace | 已完成 |
| Phase 8 | V3 Release Polish | 已完成 |

### 下一步

进入 V3 Phase 1：

1. 新建 `docs/v3/phase01-failure-taxonomy-detailed-design.md`。
2. 明确 diagnosis schema、severity、confidence、repair candidates 和测试 fixture。
3. 扩展 failure diagnosis service。
4. 验证每类 failure 都能映射到 repair candidate。

## 2026-06-26：Phase 1-4 闭环

### 当前阶段

V3 Phase 1 到 Phase 4 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### Phase 1：Failure Taxonomy 2.0

产出：

- 新增 `docs/v3/phase01-failure-taxonomy-detailed-design.md`。
- 新增 `backend/app/services/v3_failure_taxonomy.py`。
- Diagnosis 从单 reason 扩展为结构化对象：
  - `reason`
  - `severity`
  - `confidence`
  - `signals`
  - `repair_candidates`
- 支持 `retrieval_miss`、`graph_miss`、`citation_mismatch`、`unsupported_claim`、`ocr_low_confidence`、`visual_grounding_missing`、`passed`。

### Phase 2：Evidence Sufficiency Scoring

产出：

- 新增 `docs/v3/phase02-evidence-sufficiency-detailed-design.md`。
- 新增 `backend/app/services/v3_sufficiency.py`。
- 支持 answer term、citation type、claim support、graph context、OCR confidence、visual grounding 的综合评分。
- 增加关键门控：
  - answer/claim 不足时最高 `insufficient`。
  - citation type mismatch 时最高 `partial`。

### Phase 3：Repair Policy Engine

产出：

- 新增 `docs/v3/phase03-repair-policy-engine-detailed-design.md`。
- 新增 `backend/app/services/v3_repair_policy.py`。
- 将 diagnosis 映射为可执行 repair action：
  - `query_rewrite`
  - `node_type_expansion`
  - `graph_depth_expansion`
  - `citation_rerank`
  - `conservative_answer_rewrite`
  - `ocr_retry`
  - `vision_grounding_retry`

### Phase 4：Self-Correcting Agent Loop

产出：

- 新增 `docs/v3/phase04-self-correcting-agent-loop-detailed-design.md`。
- 新增 `backend/app/services/v3_self_correcting_agent.py`。
- 新增 V3 schemas：`backend/app/schemas/v3.py`。
- 新增 V3 API router：`backend/app/api/v3.py`。
- 新增 API：
  - `POST /api/v3/failure-taxonomy`
  - `POST /api/v3/sufficiency-score`
  - `POST /api/v3/repair-plan`
  - `POST /api/v3/documents/{document_id}/self-correcting-questions`
- Self-correcting loop 支持 initial run、sufficiency、diagnosis、repair plan、repair run、final sufficiency 和 repair trace。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_v3_reliability.py`：2 passed，1 warning。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：45 passed，1 warning。
- `npm run build`：Next.js production build 通过。

### 下一步

进入 V3 Phase 5：Curated Benchmark Suite。

## 2026-06-26：Phase 5-8 闭环

### 当前阶段

V3 Phase 5 到 Phase 8 已按“详细设计 -> 实现 -> 验证 -> 记录”的工作流完成。

### Phase 5：Curated Benchmark Suite

产出：

- 新增 `docs/v3/phase05-curated-benchmark-suite-detailed-design.md`。
- 新增 `eval/curated_benchmark.py`。
- 新增 curated cases：`eval/cases/v3_curated_cases.jsonl`。
- Curated case schema 包含 `expected_failure_mode`、`repair_expectation`、tags 和 source profile。

### Phase 6：Reliability Evaluation

产出：

- 新增 `docs/v3/phase06-reliability-evaluation-detailed-design.md`。
- 扩展 `eval/run_eval.py`：
  - 新增 `v3_self_correcting` strategy。
  - 输出 reliability summary。
  - 输出 failure before/after distribution。
- 生成 V3 reliability report：
  - `eval/reports/v3_reliability_report.json`
  - `eval/reports/v3_reliability_report.md`

### Phase 7：Workbench Repair Trace

产出：

- 新增 `docs/v3/phase07-workbench-repair-trace-detailed-design.md`。
- 新增 `frontend/components/repair-trace-panel.tsx`。
- Workbench 新增 V3 Repair Trace 面板。
- 前端 action/lib/types 接入 self-correcting question API。
- UI 展示 initial/final sufficiency、diagnosis、selected action 和 repair rounds。

### Phase 8：V3 Release Polish

产出：

- 新增 `docs/v3/phase08-v3-release-polish-detailed-design.md`。
- 新增 `docs/v3/v3-demo-runbook.md`。
- 新增 `docs/v3/v3-resume-bullets.md`。
- 更新 README 和 eval README。

### 验证记录

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_eval_harness.py`：3 passed，1 warning。
- `backend\.venv\Scripts\python.exe eval\run_eval.py --cases eval\cases\v3_curated_cases.jsonl --output eval\reports\v3_reliability_report.json`：生成 V3 JSON/Markdown report。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：46 passed，1 warning。
- `npm run build`：Next.js production build 通过。

### 完成状态

V3 Phase 5-8 已完成实现、测试、报告和发布文档，等待提交同步。
