# Phase 4 Detailed Design: 基础表格解析与表格证据节点

## 1. Phase 目标

Phase 4 在 Phase 3 文本证据节点的基础上，新增基础表格解析能力。系统从已渲染 PDF 中检测表格区域，提取表格 bbox、行列规模、单元格 bbox 和二维文本内容，并保存为 `table` evidence node。

本阶段的重点是让 MAGE-Doc 具备“文本 + 表格”两类可定位证据，为后续检索工具、Agent 证据检查和跨页引用打基础。

## 2. 非目标

- 不做复杂跨页表格合并。
- 不做无边框复杂表格的高级恢复。
- 不做表头层级推断。
- 不做表格语义问答。
- 不做向量化和 Agent 调用。
- 不新增独立数据库表存放表格结构。

## 3. 用户可见结果

- 用户上传 PDF 后，先渲染页面，再执行表格解析。
- 文档状态可更新为 `tables_parsed`。
- 后端可返回整篇文档或单页的 `table` evidence nodes。
- 前端页面 viewer 可显示文本块 overlay 和表格 overlay。
- 表格 overlay 展示表格数量、行列规模和表格序号。

## 4. 工具选型

### 4.1 主解析工具：PyMuPDF `page.find_tables()`

Phase 4 使用 PyMuPDF 内置 `page.find_tables()` 作为基础表格检测工具。

选择原因：

- 当前项目已安装 PyMuPDF 1.27.2.3，`find_tables()` 可用。
- 表格 bbox、cell bbox 与 Phase 2 页面渲染、Phase 3 文本块解析同源，单位均为 PDF point。
- 无需新增依赖，降低环境复杂度。
- 对 V0 的规则线表格和常见财报表格具备较好的闭环价值。

### 4.2 后续增强工具

- `pdfplumber`：后续用于对比表格提取质量和处理部分无边框表格。
- `pymupdf_layout`：PyMuPDF 官方建议的增强版页面布局分析包，后续版本可评估接入。
- OCR/layout model：V1/V2 处理扫描件、复杂多栏表格和图表。

## 5. 数据模型设计

继续使用 `evidence_nodes` 表。

`table` 节点字段：

- `node_type`: `table`
- `text`: 表格内容的轻量 Markdown/TSV 摘要，便于后续检索。
- `bbox_json`: 表格整体 bbox，格式 `[x0, y0, x1, y1]`，单位 PDF point。
- `reading_order`: 文档内证据顺序。
- `metadata_json`: 表格结构元数据：
  - `source`
  - `method`
  - `table_index`
  - `row_count`
  - `col_count`
  - `cells`
  - `matrix`

设计取舍：

- V0 不创建 `tables` 和 `table_cells` 专表，避免早期 schema 过重。
- 单元格 bbox 和二维内容放入 metadata，足以支撑前端 overlay、后续 prompt 拼接和 Agent 工具返回。
- 后续若需要表格编辑、SQL-like 查询或跨页表格合并，再抽出结构化表格表。

## 6. 后端服务设计

扩展 `backend/app/services/evidence.py`。

新增常量：

- `TABLE_NODE_TYPE = "table"`

新增能力：

- `parse_document_tables(db, document_id)`
  - 校验文档存在。
  - 校验已渲染页面存在。
  - 将文档状态置为 `parsing_tables`。
  - 打开 PDF。
  - 逐页调用 `page.find_tables()`。
  - 对每个表格提取整体 bbox、cells、row_count、col_count、matrix。
  - 删除该文档旧的 `table` 节点后重建。
  - 成功后状态置为 `tables_parsed`。
- `list_document_tables(db, document_id)`
  - 返回文档所有表格节点。
- `list_page_tables(db, document_id, page_number)`
  - 返回指定页面表格节点。

阅读顺序设计：

- V0 的 `reading_order` 对每类节点独立从 1 开始。
- 后续 Phase 5/6 建图时再统一生成跨类型 evidence ordering。

## 7. API 设计

新增接口：

```text
POST /api/documents/{document_id}/parse-tables
GET  /api/documents/{document_id}/tables
GET  /api/documents/{document_id}/pages/{page_number}/tables
```

响应仍使用 `EvidenceNodeResponse`：

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "page_id": "uuid",
  "page_number": 1,
  "node_type": "table",
  "text": "| Metric | 2025 | 2026 | ...",
  "bbox": [60.0, 80.0, 330.0, 164.0],
  "reading_order": 1,
  "metadata": {
    "source": "pymupdf",
    "method": "page.find_tables",
    "table_index": 1,
    "row_count": 3,
    "col_count": 3,
    "cells": [[60.0, 80.0, 150.0, 108.0]],
    "matrix": [["Metric", "2025", "2026"]]
  },
  "created_at": "..."
}
```

## 8. 前端交互设计

前端新增：

- 文档卡片增加 `Parse tables` 操作。
- `PageViewer` 同时接收 `textBlocks` 和 `tables`。
- 页面图上显示：
  - 文本块：绿色细框。
  - 表格：蓝色较粗框。
- 页面 metrics 展示文本块数量和表格数量。
- 表格 overlay label 显示 `T<reading_order>` 与行列规模。

## 9. 测试和验收标准

后端测试：

- 生成带规则线表格的 PDF。
- 上传、渲染、解析表格。
- 至少返回 1 个 `table` evidence node。
- 校验 bbox、row_count、col_count、matrix、cells。
- 校验单页表格过滤。
- 未渲染直接解析返回 `409`。
- 解析成功后文档状态为 `tables_parsed`。

前端验证：

- TypeScript 类型通过。
- `npm run build` 通过。
- `PageViewer` 同时渲染文本 overlay 和表格 overlay。

Smoke：

- 使用生成表格 PDF 走上传、渲染、解析表格链路。
- 输出 table count、bbox、行列规模和第一行内容。

## 10. 风险和取舍

- PyMuPDF 基础表格检测对无边框表格、跨页表格和复杂嵌套表格可能失败。V0 接受该限制，先把可定位表格证据闭环。
- 表格结构放在 metadata，不适合复杂查询。后续若做表格问答和 SQL-like 分析，再引入专门结构。
- 当前 `document.status` 是单状态字段，文本解析和表格解析会覆盖状态。V0 接受，后续可拆成 pipeline step 状态。

## 11. 完成定义

- Phase 4 详细设计完成。
- 后端表格解析 service、API、测试完成。
- 前端表格解析入口和 table overlay 完成。
- 后端测试通过。
- 前端构建通过。
- 表格解析 smoke 通过。
- README 和 Batch 1 工作日志更新。
