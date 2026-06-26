# V3 Phase 6 详细设计：Reliability Evaluation

## 1. 目标

Phase 6 的目标是在 V2 eval harness 基础上新增 V3 reliability evaluation，对比 baseline 与 self-correcting strategy，证明 repair loop 对可靠性指标有提升。

## 2. Strategy

新增 strategy：

```text
v3_self_correcting
```

对比策略：

- `v0_agent_baseline`
- `v1_evidence_pack`
- `v2_multimodal_graph`
- `v3_self_correcting`

## 3. Reliability Metrics

新增指标：

- `initial_sufficiency_score`
- `final_sufficiency_score`
- `repair_round_count`
- `repair_success_rate`
- `recovery_rate`
- `average_repair_rounds`
- `failure_before_distribution`
- `failure_after_distribution`

定义：

- recovery：初始不 sufficient，最终 partial/sufficient。
- repair success：最终 score >= 初始 score 且执行过 repair。

## 4. Report

输出：

```text
eval/reports/v3_reliability_report.json
eval/reports/v3_reliability_report.md
```

Markdown 必须包含：

- Strategy metrics table。
- Reliability summary。
- Failure before/after。
- V3 repair case table。

## 5. 验收

- Eval runner 能跑 curated cases。
- Report 包含 `v3_self_correcting`。
- 至少一个 case 有 repair round。
- JSON/Markdown report 均生成。

