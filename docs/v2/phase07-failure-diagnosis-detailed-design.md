# V2 Phase 7 详细设计：Failure Diagnosis

## 1. 目标

Phase 7 的目标是把 RAG 失败从“分数低”转换为可解释、可修复的诊断原因。它服务于两个场景：

- benchmark report 自动给出失败分布。
- API/Workbench 可以解释单个失败 case 为什么失败。

## 2. 诊断类型

| 类型 | 触发条件 | 修复方向 |
| --- | --- | --- |
| `retrieval_miss` | 没有命中期望答案或证据类型 | 调整 query rewrite、node type、hybrid 权重 |
| `graph_miss` | source candidate 有结果但 evidence pack 没扩展出上下文 | 调整 edge 类型、图构建 |
| `citation_mismatch` | 答案有关键词但 citation 类型不匹配 | 调整 citation selection |
| `unsupported_claim` | claim verification 为 unsupported/insufficient | 增强证据 pack 或回答约束 |
| `ocr_low_confidence` | case 依赖 OCR 且 OCR confidence 低 | 换 OCR adapter 或人工复核 |
| `visual_grounding_missing` | case 依赖图表/视觉节点但未命中 | 加强 figure/chart detection |
| `passed` | 所有关键指标通过 | 无需修复 |

## 3. Service 设计

新增模块：

```text
backend/app/services/v2_failure_diagnosis.py
```

核心函数：

- `diagnose_result(case, result) -> dict`
- `summarize_diagnoses(diagnoses) -> dict`
- `diagnose_results(cases, results) -> dict`

输入兼容 eval result：

```json
{
  "case_id": "case-001",
  "strategy": "v2_multimodal_graph",
  "answer_term_hit": 0.0,
  "citation_node_type_hit": 0.0,
  "claim_supported": 0.0,
  "evidence_pack_context_hit": 0.0
}
```

## 4. API 设计

新增 API：

```text
POST /api/v2/failure-diagnosis
```

请求：

```json
{
  "cases": [],
  "results": []
}
```

响应：

```json
{
  "case_count": 2,
  "result_count": 6,
  "distribution": {"retrieval_miss": 2},
  "diagnoses": []
}
```

## 5. 验收

- 对 retrieval miss、citation mismatch、unsupported claim 至少有测试覆盖。
- eval report 中包含 failure summary。
- API 能返回 distribution 和 per-case diagnosis。

