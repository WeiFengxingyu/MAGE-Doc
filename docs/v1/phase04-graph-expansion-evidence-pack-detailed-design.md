# V1 Phase 4 详细设计：Graph Expansion 与 Evidence Pack

## 1. Phase 目标

Phase 4 的目标是把 Phase 3 的 hybrid retrieval candidates 升级成可供 Agent 回答和验证使用的 **Evidence Pack**。

V0 和 Phase 3 的检索结果仍然是“若干 top-k 节点”。Phase 4 要解决的问题是：

> top-k 节点本身往往不够回答长文档问题，Agent 还需要章节上下文、表格单元格、caption、相邻文本块和证据路径。

因此本阶段新增：

- graph expansion service。
- evidence pack 数据结构。
- evidence pack API。
- inclusion reason、graph distance、edge path 和 source candidate 追踪。

## 2. 非目标

- 不在本阶段生成最终自然语言答案。
- 不做 claim-level verification，Phase 6 处理。
- 不引入 LLM planner。
- 不实现无限图遍历或复杂路径搜索。

## 3. 输入与输出

### 3.1 输入

```text
document_id
query
top_k
depth
edge_types
node_types
```

默认：

- `top_k = 3`
- `depth = 1`
- `edge_types = contains,next,part_of,caption_of,near`
- `node_types = text_block,table`

### 3.2 输出

Evidence Pack 包含：

- query。
- source candidates。
- expanded nodes。
- expanded edges。
- evidence items。
- summary stats。
- tool trace。

核心结构：

```json
{
  "query": "...",
  "document_id": "...",
  "source_candidates": [],
  "nodes": [],
  "edges": [],
  "items": [
    {
      "node": {},
      "source_candidate_node_id": "...",
      "graph_distance": 0,
      "inclusion_reason": "source_candidate",
      "path": []
    }
  ],
  "summary": {
    "source_candidate_count": 3,
    "expanded_node_count": 8,
    "edge_count": 10,
    "max_graph_distance": 1
  }
}
```

## 4. Graph Expansion 策略

### 4.1 候选来源

先调用现有 `search_evidence`：

- 保留 Phase 3 的 hybrid scoring。
- source candidate distance = 0。
- inclusion reason = `source_candidate`。

### 4.2 扩展边

默认扩展边：

| 边类型 | 方向 | 作用 |
| --- | --- | --- |
| `contains` | incoming/outgoing | 找 section/page 上下文 |
| `next` | incoming/outgoing | 找阅读顺序相邻块 |
| `part_of` | incoming/outgoing | table 与 cell 互相定位 |
| `caption_of` | incoming/outgoing | table 与 caption 互相定位 |
| `near` | outgoing | 版面邻近证据 |

### 4.3 扩展限制

- `depth` 最大限制为 2。
- 每个 source candidate 每一层最多扩展 12 条边。
- 所有节点去重。
- 所有边去重。
- source candidate 优先级最高，扩展节点不覆盖 source candidate 的 rank。

## 5. Evidence Item 排序

排序规则：

1. source candidate 排在扩展节点前。
2. graph distance 小的排前。
3. source candidate rank 小的排前。
4. 同页 reading_order 小的排前。
5. table/caption/cell 根据 inclusion reason 保留在相关 candidate 附近。

## 6. Inclusion Reason

| reason | 含义 |
| --- | --- |
| `source_candidate` | hybrid retrieval 直接召回 |
| `contains_context` | section/page contains 关系扩展 |
| `reading_order_context` | next 关系扩展 |
| `table_structure_context` | part_of 关系扩展 |
| `caption_context` | caption_of 关系扩展 |
| `layout_near_context` | near 关系扩展 |

## 7. API 设计

新增 API：

```text
GET /api/documents/{document_id}/evidence-pack
```

Query 参数：

- `query`
- `top_k`
- `depth`
- `node_types`
- `edge_types`

## 8. Schema 设计

新增 schema：

- `EvidencePackCandidateResponse`
- `EvidencePackItemResponse`
- `EvidencePackSummaryResponse`
- `EvidencePackResponse`

## 9. Service 设计

新增文件：

- `backend/app/services/evidence_pack.py`
- `backend/app/schemas/evidence_pack.py`
- `backend/app/tests/test_evidence_pack.py`

核心函数：

- `build_evidence_pack(...)`
- `expand_candidate_neighborhood(...)`
- `edge_reason(edge_type)`
- `pack_item(...)`

## 10. 前端影响

Phase 4 不强制新增 UI 面板，但需要同步 TypeScript 类型，方便 Phase 8 直接展示 Evidence Pack。

新增类型：

- `EvidenceEdge`
- `EvidencePackItem`
- `EvidencePackResponse`

## 11. 测试策略

新增测试覆盖：

- evidence pack API 能基于 query 返回 source candidates。
- pack 包含 source candidate 和扩展节点。
- table query 能通过 `part_of` 或 `caption_of` 扩展到 table_cell/caption。
- `depth=0` 时只返回 source candidates。
- tool trace 输出 evidence pack 构建摘要。

## 12. 验收标准

- `pytest backend/app/tests/test_evidence_pack.py` 通过。
- graph、retrieval、agent 回归测试通过。
- 前端 build 通过。
- 工作日志记录 Phase 4 实现和验证。
- 形成本地 commit，并尝试推送 GitHub。

## 13. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| graph expansion 噪声过多 | pack 不够聚焦 | 限制 depth、edge_types 和 per-layer edge budget |
| source candidate 与扩展节点混排混乱 | Agent 难以解释 | item 中保留 source_candidate_node_id、distance、reason 和 path |
| Phase 4 过早接入 Agent | 影响 V0 稳定性 | 本阶段只新增独立 evidence pack API |
