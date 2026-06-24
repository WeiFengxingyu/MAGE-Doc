# V1 Phase 1 详细设计：Evidence Graph 数据模型

## 1. Phase 目标

Phase 1 的目标是把 V0 已经存在的 document、page、text_block、table 证据组织成可查询的 evidence graph。

本阶段不追求复杂图推理，只建立后续 V1 的底座：

- 新增 `EvidenceEdge` 数据模型。
- 新增 graph service，支持构图、邻域查询、边去重和子图导出。
- 新增 graph API，让前端和后续 Agent 可以读取图结构。
- 为已解析文档生成基础 `contains` 和 `next` 边。

## 2. 非目标

- 不引入 Neo4j、NetworkX 持久化或独立图数据库。
- 不实现完整 section/caption/cell 关系，这些进入 Phase 2。
- 不改造 V0 问答流程。
- 不引入 graph-based rerank，这些进入 Phase 3 和 Phase 4。

## 3. 用户可见结果

用户在后端 API 层可以：

- 对一个文档调用 graph build API。
- 查询文档 graph summary。
- 给定 evidence node 查询邻域。
- 看到 graph 中的节点、边、edge type、source 和 metadata。

## 4. 数据模型

新增表：`evidence_edges`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string uuid | 边 ID |
| `document_id` | string | 所属文档 |
| `source_node_id` | string nullable | 起点 evidence node，page/document 虚拟节点可为空 |
| `target_node_id` | string | 终点 evidence node |
| `edge_type` | string | `contains`、`next` 等 |
| `weight` | float | 默认 1.0 |
| `source` | string | 构边来源，例如 `phase1_graph_builder` |
| `metadata_json` | text | page_number、reading_order、reason 等 |
| `created_at` | datetime | 创建时间 |

约束：

- 同一文档内 `(source_node_id, target_node_id, edge_type, source)` 唯一。
- `target_node_id` 级联删除。
- `source_node_id` 允许为空，用于 document/page 这类虚拟层级边。

## 5. Graph 构建规则

Phase 1 只生成基础边：

1. **page_contains**
   - 虚拟 page -> evidence node。
   - `source_node_id = null`。
   - `target_node_id = evidence node id`。
   - `edge_type = contains`。
   - metadata 保存 `container_type=page`、`page_id`、`page_number`。

2. **next**
   - 同一文档阅读顺序中的相邻 evidence node。
   - 按 `page_number`、`reading_order`、`created_at` 排序。
   - `source_node_id = previous evidence node id`。
   - `target_node_id = next evidence node id`。
   - metadata 保存相邻节点的 page 和 reading_order。

## 6. API 设计

新增 API：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/api/documents/{document_id}/graph/build` | 构建基础 evidence graph |
| `GET` | `/api/documents/{document_id}/graph` | 返回 graph summary 和边列表 |
| `GET` | `/api/documents/{document_id}/graph/neighbors/{node_id}` | 查询节点邻域 |

## 7. Service 设计

新增文件：

- `backend/app/models/graph.py`
- `backend/app/schemas/graph.py`
- `backend/app/services/graph.py`
- `backend/app/tests/test_graph.py`

核心函数：

- `build_document_graph(db, document_id)`
- `list_document_graph(db, document_id)`
- `get_node_neighbors(db, document_id, node_id)`
- `upsert_edge(...)`

## 8. 测试策略

新增后端测试覆盖：

- 文档上传、渲染、文本解析后可以构建 graph。
- graph build 幂等，重复调用不重复创建边。
- page contains 边数量等于 evidence node 数量。
- next 边数量等于 evidence node 数量减一。
- neighbor API 能查到 incoming 和 outgoing edges。

## 9. 验收标准

- `pytest backend/app/tests/test_graph.py` 通过。
- 全量后端测试通过。
- README 或流程文档能找到 Phase 1 详细设计入口。
- `docs/v1/batch2-worklog.md` 记录本 Phase 的实现和验证结果。

## 10. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| SQLite 无递归图查询优化 | 大图查询性能有限 | V1 初期只查局部邻域，足够支持 demo |
| 虚拟 page/document 节点未入库 | 层级表达不够统一 | Phase 1 先用 edge metadata 表达，Phase 2 再补 section/cell 节点 |
| 无迁移框架 | 已有数据库表结构升级有限 | 当前项目仍是本地 demo，沿用 `create_all`；必要时后续引入 Alembic |
