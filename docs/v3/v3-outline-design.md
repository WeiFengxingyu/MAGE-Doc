# MAGE-Doc V3 概要设计：Failure-Aware Self-Correcting Agentic RAG

## 1. V3 定位

V3 的目标不是继续横向堆功能，而是把 V2 的多模态 Agent 平台深化为 **面向可靠性的自诊断、自修复 Agentic RAG 系统**。

V2 已经完成：

```text
OCR + Vision Grounding + Metric Graph + Collection + MCP Tools + Benchmark Adapter + Failure Diagnosis
```

V3 要解决的问题是：

> 当 Agentic RAG 在长文档、多模态、多证据问题上答错时，系统能否判断错在哪里，并自动选择下一步修复策略，而不是只返回一个失败答案？

V3 的核心主题：

```text
Failure Diagnosis -> Repair Policy -> Self-Correcting Agent Loop -> Benchmark-Proven Reliability
```

## 2. 与 V2 的关键区别

| 维度 | V2 | V3 |
| --- | --- | --- |
| 目标 | 平台化能力完整 | 可靠性和自修复能力 |
| 失败处理 | 输出 failure diagnosis | 根据 diagnosis 自动执行 repair action |
| Agent 行为 | 固定工具链/单轮 evidence pack | 多轮策略选择、反思、重试和保守回答 |
| 评测 | V2 benchmark report | repair 前后对比、失败恢复率、成本/延迟权衡 |
| 数据集 | synthetic + benchmark adapter | curated real/semi-real long-doc benchmark |
| 简历价值 | 多模态 Agent 平台 | benchmark-driven reliable Agentic RAG |

## 3. V3 必须完成

- Failure taxonomy 结构化升级：把 V2 的诊断结果扩展为可执行 repair signal。
- Repair policy engine：根据 failure reason 选择 query rewrite、node type expansion、graph depth increase、citation rerank、answer rewrite 等动作。
- Self-correcting agent loop：支持 plan -> retrieve -> verify -> diagnose -> repair -> final 的多轮执行。
- Evidence sufficiency scoring：判断证据是否足够支撑答案，避免硬答和幻觉。
- Benchmark suite：构建一组真实或半真实长文档 case，标注 expected answer、evidence node type、page、bbox、failure mode。
- Reliability dashboard/report：展示修复前后指标、失败分布、恢复率、平均工具调用、延迟。

## 4. V3 非目标

- 不训练大模型。
- 不追求生产级大规模评测平台。
- 不用不可解释的 prompt 堆叠替代可测试策略。
- 不把 repair 做成无限循环，默认限制最多 2 到 3 轮。
- 不为了外部 benchmark 破坏本地可运行闭环。

## 5. 总体架构

```text
User Question / Benchmark Case
   |
   v
Initial Agent Run
   |-- search_doc
   |-- build_evidence_pack
   |-- inspect_page / read_table
   |-- verify_claims
   v
Evidence Sufficiency Judge
   |
   v
Failure Diagnosis
   |-- retrieval_miss
   |-- graph_miss
   |-- citation_mismatch
   |-- unsupported_claim
   |-- ocr_low_confidence
   |-- visual_grounding_missing
   v
Repair Policy Engine
   |-- query_rewrite
   |-- node_type_expansion
   |-- graph_depth_expansion
   |-- citation_rerank
   |-- visual_or_ocr_retry
   |-- conservative_answer_rewrite
   v
Self-Correcting Agent Loop
   |
   v
Final Answer + Citations + Trace + Repair Report
   |
   v
Reliability Evaluation Dashboard
```

## 6. 核心模块

### 6.1 Failure Taxonomy 2.0

目标：

- 将 failure reason 从 report 字符串升级为结构化对象。
- 每个 diagnosis 包含 severity、confidence、repair_candidates、evidence_signals。
- 支持多标签：例如同时存在 `retrieval_miss` 和 `visual_grounding_missing`。

输出示例：

```json
{
  "reason": "citation_mismatch",
  "severity": "medium",
  "confidence": 0.82,
  "repair_candidates": ["citation_rerank", "graph_depth_expansion"],
  "signals": {"answer_term_hit": 1.0, "citation_node_type_hit": 0.0}
}
```

### 6.2 Repair Policy Engine

目标：

- 根据 diagnosis 选择下一步工具计划。
- 控制修复成本，避免无限循环。
- 每次 repair action 都写入 trace。

策略映射：

| Failure | Repair Action |
| --- | --- |
| `retrieval_miss` | query rewrite + node type expansion |
| `graph_miss` | graph depth expansion + extra edge types |
| `citation_mismatch` | citation rerank + required node type filter |
| `unsupported_claim` | conservative answer rewrite + verify claims |
| `ocr_low_confidence` | OCR retry or human-review flag |
| `visual_grounding_missing` | vision grounding retry + visual node search |

### 6.3 Self-Correcting Agent Loop

目标：

- 将现有 deterministic agent 扩展为可靠性优先的多轮 agent。
- 每轮记录工具调用、诊断、repair action、指标变化。
- 最终答案必须带 citations 和 confidence。

默认 loop：

```text
run_initial -> verify -> diagnose -> repair_if_needed -> verify_again -> final
```

停止条件：

- claim verification supported。
- evidence sufficiency score 达标。
- 达到最大 repair rounds。
- repair action 不再带来指标提升。

### 6.4 Evidence Sufficiency Scoring

目标：

- 不只判断有没有 citation，还要判断 citation 是否足够。
- 评分信号包括 answer term hit、citation type hit、claim support、graph context hit、OCR confidence、visual grounding availability。

输出：

```json
{
  "score": 0.78,
  "label": "sufficient",
  "missing_signals": ["visual_evidence"],
  "recommended_policy": "visual_grounding_retry"
}
```

### 6.5 Curated Long-Doc Benchmark

目标：

- 从 synthetic case 升级到 curated case。
- 支持 annual report、technical manual、paper、policy doc 四类文档。
- 每个 case 标注：
  - question。
  - answer terms。
  - expected evidence node types。
  - expected page。
  - expected bbox 或 evidence id。
  - expected failure mode。

### 6.6 Reliability Dashboard

目标：

- 在 Workbench 中展示 repair trace。
- 在 eval report 中展示：
  - baseline pass rate。
  - repaired pass rate。
  - recovery rate。
  - average repair rounds。
  - average latency。
  - failure distribution before/after。

## 7. 数据模型方向

新增或扩展：

| 模型 | 说明 |
| --- | --- |
| `repair_runs` | 单次 self-correction run |
| `repair_steps` | 每轮 diagnosis/action/result |
| `sufficiency_scores` | 证据充分性评分记录 |
| `benchmark_cases` | curated benchmark case metadata |
| `benchmark_case_labels` | expected evidence/failure labels |

Trace 扩展：

- `repair_round`
- `failure_reason`
- `repair_action`
- `before_metrics`
- `after_metrics`
- `stop_reason`

## 8. 技术选型

| 模块 | 默认选型 | 原因 |
| --- | --- | --- |
| Diagnosis | Rule-based + calibrated score | 可解释、可测试 |
| Repair policy | Deterministic policy table first | 适合简历演示和单测 |
| Query rewrite | Template + optional LLM adapter | 无外部依赖可闭环 |
| Sufficiency judge | Weighted scoring | 指标透明 |
| Benchmark | JSONL + local PDFs | 延续 V1/V2 eval harness |
| Dashboard | Next.js compact evaluation panel | 和现有 workbench 一致 |

## 9. V3 验收线

V3 完成时应满足：

- 至少 5 类 failure reason 能映射到 repair action。
- Self-correcting agent 能在失败 case 上执行至少 1 轮 repair，并记录 trace。
- Eval report 能对比 baseline 与 repaired strategy。
- Report 至少包含 recovery rate、repair rounds、failure before/after。
- Workbench 能展示某个回答的 diagnosis 和 repair path。
- README、runbook、简历 bullets 更新。

## 10. 简历表达目标

V3 完成后可支撑：

- 在多模态 Evidence Graph Agentic RAG 基础上，设计 failure-aware self-correction loop，使系统能对 retrieval miss、citation mismatch、unsupported claim 等失败自动诊断并执行修复策略。
- 构建 benchmark-driven reliability evaluation，对比修复前后 claim support rate、citation accuracy、recovery rate 和平均工具调用成本。
- 实现可解释 repair trace，将每轮诊断、工具调用、证据充分性评分和最终答案统一记录，提升长文档 RAG 的可观测性和可信度。

