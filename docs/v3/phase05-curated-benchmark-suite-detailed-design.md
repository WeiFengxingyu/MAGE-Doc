# V3 Phase 5 详细设计：Curated Benchmark Suite

## 1. 目标

Phase 5 的目标是把 V3 从单个 demo case 推进到可重复、可标注、可扩展的 reliability benchmark suite。该 benchmark 不追求规模，而追求每个 case 都带明确证据标签和预期 failure mode。

## 2. Case Schema

每行 JSONL 一个 case：

```json
{
  "id": "curated_table_revenue_2026",
  "question": "What was revenue in 2026?",
  "question_type": "table_lookup",
  "expected_answer_terms": ["Revenue", "128", "2026"],
  "expected_node_types": ["table", "metric_value"],
  "expected_failure_mode": "citation_mismatch",
  "repair_expectation": "citation_rerank",
  "tags": ["table", "metric", "repairable"],
  "source_profile": "synthetic_financial_report"
}
```

必填字段：

- `id`
- `question`
- `question_type`
- `expected_answer_terms`
- `expected_node_types`
- `expected_failure_mode`

可选字段：

- `repair_expectation`
- `tags`
- `source_profile`
- `notes`

## 3. Case 覆盖

V3 第一批 curated cases 至少覆盖：

- text lookup。
- table lookup。
- metric lookup。
- graph/context lookup。
- failure-aware repairable case。

后续 V3 Phase 5 可继续扩展 OCR、visual、cross-doc case。

## 4. 实现位置

新增：

```text
eval/curated_benchmark.py
eval/cases/v3_curated_cases.jsonl
```

核心函数：

- `load_curated_cases(path)`
- `validate_curated_case(row)`
- `case_failure_targets(cases)`

## 5. 验收

- JSONL loader 能读取 curated cases。
- 缺少必填字段时给出明确错误。
- 至少 5 个 case 可被 eval runner 使用。

