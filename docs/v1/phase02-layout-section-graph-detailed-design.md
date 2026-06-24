# V1 Phase 2 详细设计：Layout 关系与 Section 构建

## 1. Phase 目标

Phase 2 的目标是在 Phase 1 基础图之上加入更有语义的 layout 关系，让 evidence graph 不只是线性节点列表，而能表达：

- 页面内的 section candidate。
- section 对 text/table 的包含关系。
- table 到 table_cell 的结构关系。
- table 附近 caption candidate。
- 同页 bbox 邻近关系。

这些关系会在 Phase 4 的 graph expansion 和 Phase 6 的 claim verification 中成为核心证据上下文。

## 2. 非目标

- 不训练标题识别、caption 检测或表格结构模型。
- 不做跨页表格合并。
- 不把 figure 视觉理解作为主路径。
- 不要求 section/caption 100% 准确；本阶段先用可解释 heuristic。

## 3. 节点扩展

新增 evidence node 类型：

| 节点类型 | 来源 | 说明 |
| --- | --- | --- |
| `section` | text_block heuristic | 标题或章节候选 |
| `table_cell` | table metadata matrix/cells | 单元格级证据 |
| `caption` | table 附近 text_block | 表格说明候选 |

## 4. 边扩展

| 边类型 | 起点 | 终点 | 说明 |
| --- | --- | --- | --- |
| `contains` | section | text/table | section 包含正文或表格 |
| `part_of` | table_cell | table | cell 属于 table |
| `caption_of` | caption | table | caption 解释 table |
| `near` | evidence node | evidence node | 同页 bbox 邻近 |

Phase 2 会继续保留 Phase 1 的 page `contains` 和 `next` 边。

## 5. Section Heuristic

section candidate 识别规则：

- 文本长度小于等于 80。
- 行数小于等于 2。
- 不是明显句子段落，末尾不以句号结尾。
- 或匹配 `1.`、`1.1`、`I.`、`A.` 这类章节编号。

构建策略：

- 每页维护当前 section。
- 遇到 section candidate 时创建 `section` 节点。
- 后续 text/table 节点通过 `contains` 边挂到当前 section。
- 如果某页没有 section，则不强行创建虚拟 section。

## 6. Table Cell 构建

从 table node 的 metadata 中读取：

- `matrix`
- `cells`
- `row_count`
- `col_count`

为每个 matrix cell 创建 `table_cell` 节点：

- text = 单元格文本。
- bbox = 对应 cell bbox；如果缺失则回退到 table bbox。
- reading_order = table reading_order * 10000 + row_index * 100 + col_index。
- metadata 包含 table_id、row_index、col_index、is_header。

边：

- `table_cell -> table` 的 `part_of`。

## 7. Caption Candidate 构建

caption 先采用简单规则：

- 与 table 同页。
- text_block 的 bbox 在 table 上方或下方一定距离内。
- 文本包含 `table`、`表`、`caption`、`figure`、`图` 等词，或长度较短。

构建 caption 节点后：

- `caption -> table` 建 `caption_of` 边。
- caption metadata 保存 source_text_node_id 和 table_id。

## 8. Near 边构建

同页节点之间按 bbox 中心点距离建立 `near` 边：

- 只在同一页内建立。
- 距离阈值默认 120 PDF points。
- 每个节点最多保留最近 3 个邻居。
- metadata 保存 distance。

## 9. API 影响

沿用 Phase 1 API：

- `POST /api/documents/{document_id}/graph/build`
- `GET /api/documents/{document_id}/graph`
- `GET /api/documents/{document_id}/graph/neighbors/{node_id}`

Phase 2 不新增 API，只扩展 graph build 输出的节点和边。

## 10. 测试策略

新增或扩展 graph 测试：

- 构建 graph 后包含 `table_cell` 节点。
- 表格节点能查到 `table_cell` 相关边。
- 文档中标题文本可生成 `section` 节点。
- table 附近短文本可生成 `caption` 节点和 `caption_of` 边。
- 同页节点之间能生成受限数量的 `near` 边。

## 11. 验收标准

- Phase 1 graph 测试继续通过。
- 新增 Phase 2 graph enrichment 测试通过。
- Graph API 返回 section、table_cell、caption 这类 V1 节点。
- `docs/v1/batch2-worklog.md` 记录本 Phase 的实现和验证结果。

## 12. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| heuristic 识别错误 | graph 中存在噪声边 | metadata 保留来源和规则，后续可替换 |
| table cell bbox 数量与 matrix 不一致 | 单元格定位不完整 | 缺失 bbox 时回退 table bbox |
| near 边过多 | graph expansion 噪声增大 | 限制同页、阈值和每节点 top-k |
