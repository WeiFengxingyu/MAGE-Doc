# V3 Phase 1 详细设计：Failure Taxonomy 2.0

## 1. 目标

Phase 1 的目标是把 V2 的单一 failure reason 升级为可执行的结构化诊断对象。V3 的 self-correction 不应只知道“失败了”，还要知道：

- 失败类型。
- 严重程度。
- 置信度。
- 触发信号。
- 推荐 repair candidates。

## 2. 输入

兼容 V2 eval result：

```json
{
  "case_id": "case-001",
  "strategy": "v2_multimodal_graph",
  "answer_term_hit": 0.0,
  "citation_node_type_hit": 0.0,
  "claim_supported": 0.0,
  "evidence_pack_context_hit": 0.0,
  "ocr_average_confidence": 0.42
}
```

兼容在线 agent run：

```json
{
  "question": "...",
  "search_result_count": 0,
  "citation_count": 0,
  "claim_status": "unsupported",
  "node_type_counts": {}
}
```

## 3. 输出

```json
{
  "reason": "retrieval_miss",
  "severity": "high",
  "confidence": 0.92,
  "message": "No answer terms or expected evidence types were recovered.",
  "signals": {},
  "repair_candidates": ["query_rewrite", "node_type_expansion"]
}
```

## 4. 分类规则

| Failure | 条件 | Severity | Repair Candidates |
| --- | --- | --- | --- |
| `retrieval_miss` | answer hit = 0 且 citation hit = 0 | high | query rewrite, node type expansion |
| `graph_miss` | 有 source candidate 但 graph context = 0 | medium | graph depth expansion, edge type expansion |
| `citation_mismatch` | answer hit > 0 且 citation type hit = 0 | medium | citation rerank, required type filter |
| `unsupported_claim` | claim supported = 0 | high | conservative answer rewrite, evidence pack retry |
| `ocr_low_confidence` | OCR confidence < 0.5 | medium | OCR retry, human review flag |
| `visual_grounding_missing` | 期望 visual evidence 但未命中 | medium | vision grounding retry, visual node search |
| `passed` | 关键指标均通过 | none | none |

## 5. 实现位置

新增：

```text
backend/app/services/v3_failure_taxonomy.py
```

核心函数：

- `diagnose_failure(case, result)`
- `diagnose_failures(cases, results)`
- `diagnosis_distribution(diagnoses)`

## 6. 验收

- 每个 failure reason 都能输出 severity、confidence、repair candidates。
- 支持 batch diagnosis。
- API 和 self-correcting agent 可以复用同一套 diagnosis schema。

