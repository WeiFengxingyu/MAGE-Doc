# V1 Phase 3 详细设计：Hybrid Retrieval Index

## 1. Phase 目标

Phase 3 的目标是把 V0 的单一路径 BM25 风格检索升级为 V1 的 hybrid retrieval 基础层。

本阶段不追求外部向量数据库或大模型 reranker，而是先建立统一 candidate 抽象：

```text
lexical candidate + semantic fallback candidate + metadata/context signal -> hybrid ranked result
```

后续 Phase 4 的 graph expansion 会直接消费这些 retrieval candidates。

## 2. 非目标

- 不接入强制外部 embedding API。
- 不部署向量数据库。
- 不实现复杂 neural reranker。
- 不改造 V0 Agent 问答主流程，只让它自然获得更丰富的检索结果。

## 3. 兼容性要求

现有接口：

```text
GET /api/documents/{document_id}/search
```

必须继续返回：

- `rank`
- `score`
- `matched_terms`
- `snippet`
- `node`

新增字段必须是向后兼容的：

- `retrieval_source`
- `score_breakdown`
- `candidate_sources`

这样现有前端和测试无需大改，V1 前端可以逐步使用新增信息。

## 4. Hybrid Candidate 设计

每个候选节点计算三类信号：

| 信号 | 说明 |
| --- | --- |
| `lexical_score` | 延续 V0 BM25 风格打分 |
| `semantic_score` | 本地 fallback embedding 相似度 |
| `metadata_score` | table/header/caption/section 等结构化提示 |

最终分数：

```text
hybrid_score = lexical_score * 0.65 + semantic_score * 0.25 + metadata_score * 0.10
```

如果 query 和文档无法产生有效 token，则返回空结果。

## 5. Semantic Fallback Adapter

为了不引入外部依赖，Phase 3 的 semantic adapter 使用本地 token hashing 向量：

- 使用现有 `_tokenize`。
- 对 token 做稳定 hash，映射到固定维度稀疏向量。
- 使用 cosine similarity。
- 后续可以替换为 BGE/OpenAI/其他 embedding provider。

Adapter contract：

```python
class EmbeddingAdapter:
    def score(query: str, text: str) -> float:
        ...
```

## 6. Metadata Score

metadata score 用来体现 V1 graph/layout 信息：

- query 包含数字或年份，table/table_cell 提升。
- query 包含 table/表/metric/指标，table/table_cell 提升。
- query 包含 summary/概括/原因，section/caption/text_block 提升。
- 节点 metadata 中有 `is_header`，对表头相关 query 提升。

## 7. API Schema 变化

`SearchResultResponse` 新增：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `retrieval_source` | string | `hybrid`、`lexical`、`semantic` |
| `candidate_sources` | list[string] | 命中的候选来源 |
| `score_breakdown` | dict | lexical、semantic、metadata 分数 |

`SearchResponse.tool_trace.output_summary` 改为描述 hybrid candidate 数量。

## 8. 测试策略

新增或更新检索测试：

- 原有 text/table 检索继续通过。
- 搜索结果包含 `retrieval_source`、`candidate_sources` 和 `score_breakdown`。
- 只有语义近似但关键词较少时，semantic fallback 仍能产生候选。
- table query 对 table 节点有 metadata boost。

## 9. 验收标准

- `pytest backend/app/tests/test_retrieval.py` 通过。
- 全量后端测试通过。
- 前端 build 通过，证明 schema 兼容。
- 工作日志记录 Phase 3 实现和验证。

## 10. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| hash embedding 语义能力有限 | 召回提升有限 | 先保证 adapter 和接口形态，后续替换真 embedding |
| hybrid score 参数主观 | 排序可能不稳定 | score breakdown 暴露出来，便于后续评测调参 |
| metadata boost 过强 | table query 可能过拟合 | boost 只占 10%，保守控制 |
