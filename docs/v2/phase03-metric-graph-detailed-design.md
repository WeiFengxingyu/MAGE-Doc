# V2 Phase 3 详细设计：Metric Graph

## 1. Phase 目标

Phase 3 的目标是把表格和文本中的指标、年份、数值抽取成 `metric_value` 节点，并通过 `derived_from`、`same_metric` 等边连接来源证据。

这让系统不只“读表格”，还可以围绕指标进行结构化推理。

## 2. 非目标

- 不做复杂财务口径归一。
- 不做多币种换算。
- 不训练信息抽取模型。

## 3. 节点类型

新增：

- `metric_value`

metadata：

- `metric_name`
- `year`
- `value`
- `unit`
- `source_table_id`
- `source_cell_ids`

## 4. 抽取规则

Phase 3 先支持 table matrix：

- 第一行为 header。
- 第一列为 metric name。
- 数字列 header 识别年份。
- 单元格值识别 number/percent。

## 5. API

新增：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/api/documents/{document_id}/metric-graph/build` | 构建 metric graph |
| `GET` | `/api/documents/{document_id}/metric-values` | 查看 metric_value 节点 |

## 6. 测试策略

- Revenue 2025/2026 表格生成 metric_value。
- metric_value 与 table 之间有 `derived_from` 边。
- search `Revenue 2026` 可召回 metric_value。

## 7. 验收标准

- Phase 3 详细设计存在。
- Metric graph API、服务和测试完成。
- 后端相关测试通过。
- 工作日志更新。
