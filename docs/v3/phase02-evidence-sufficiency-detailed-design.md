# V3 Phase 2 详细设计：Evidence Sufficiency Scoring

## 1. 目标

Phase 2 的目标是建立证据充分性评分，让系统判断“当前证据是否足够回答问题”，而不是只依赖 citation 是否存在。

## 2. 评分信号

| Signal | 权重 | 说明 |
| --- | --- | --- |
| `answer_term_hit` | 0.25 | 答案关键项是否出现 |
| `citation_node_type_hit` | 0.20 | citation 类型是否符合预期 |
| `claim_supported` | 0.25 | claim verification 是否支持 |
| `evidence_pack_context_hit` | 0.15 | graph expansion 是否提供上下文 |
| `ocr_confidence` | 0.075 | OCR 相关 case 的置信度 |
| `visual_grounding` | 0.075 | visual 相关 case 是否命中视觉证据 |

## 3. 输出

```json
{
  "score": 0.78,
  "label": "sufficient",
  "missing_signals": ["visual_grounding"],
  "recommended_policy": "vision_grounding_retry"
}
```

## 4. Label 规则

- `sufficient`：score >= 0.75。
- `partial`：0.45 <= score < 0.75。
- `insufficient`：score < 0.45。

## 5. 实现位置

新增：

```text
backend/app/services/v3_sufficiency.py
```

核心函数：

- `score_evidence(case, result)`
- `score_agent_answer(question, answer_payload)`

## 6. 验收

- supported claim + matching citation 能达到 sufficient。
- retrieval miss 会得到 insufficient。
- citation mismatch 或 unsupported claim 能给出 missing signals 和 recommended policy。

