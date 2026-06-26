# V3 Phase 3 详细设计：Repair Policy Engine

## 1. 目标

Phase 3 的目标是把 failure diagnosis 转换为可执行 repair action。Repair policy engine 是 V3 self-correcting agent 的决策层。

## 2. Repair Action Schema

```json
{
  "action": "node_type_expansion",
  "reason": "retrieval_miss",
  "description": "Retry retrieval across all multimodal node types.",
  "tool_plan": ["search_evidence", "build_evidence_pack"],
  "arguments": {"node_types": null, "top_k": 5},
  "cost_level": "low",
  "stop_rule": "stop_if_results_found"
}
```

## 3. Policy Table

| Diagnosis | Primary Action | Secondary Action |
| --- | --- | --- |
| `retrieval_miss` | `query_rewrite` | `node_type_expansion` |
| `graph_miss` | `graph_depth_expansion` | `edge_type_expansion` |
| `citation_mismatch` | `citation_rerank` | `required_type_filter` |
| `unsupported_claim` | `conservative_answer_rewrite` | `evidence_pack_retry` |
| `ocr_low_confidence` | `ocr_retry` | `human_review_flag` |
| `visual_grounding_missing` | `vision_grounding_retry` | `visual_node_search` |

## 4. 实现位置

新增：

```text
backend/app/services/v3_repair_policy.py
```

核心函数：

- `select_repair_actions(diagnosis, max_actions=2)`
- `build_repair_plan(diagnoses)`

## 5. 验收

- 每个 failure reason 至少映射 1 个 action。
- action 可序列化进入 trace。
- passed diagnosis 不生成 repair action。

