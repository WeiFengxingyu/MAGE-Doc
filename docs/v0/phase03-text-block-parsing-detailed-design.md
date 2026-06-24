# Phase 3 Detailed Design: 文本块解析与证据节点

## 1. Phase 目标

Phase 3 将 Phase 2 已建立的页面坐标系统向“真实证据”推进：从已上传并已渲染的 PDF 中解析文本块，保存文本内容、页面归属、阅读顺序和 bbox 坐标，并在前端页面图片上展示真实文本块 overlay。

本阶段的核心产物不是一个临时 parser，而是后续多模态证据图的第一类节点：`text_block` evidence node。

## 2. 非目标

- 不做 OCR。
- 不做表格结构识别。
- 不做图片、图表和公式检测。
- 不做向量索引和语义检索。
- 不做 Agent 问答。
- 不引入独立布局模型或视觉大模型。

## 3. 用户可见结果

- 用户上传 PDF 后，先执行页面渲染，再执行文本块解析。
- 文档状态从 `rendered` 进入 `parsed`。
- 页面 viewer 上展示真实文本块框，而不是 Phase 2 的测试 bbox。
- 后端可返回整篇文档或单页的文本块列表。

## 4. 工具选型

### 4.1 主解析工具：PyMuPDF

Phase 3 继续使用 PyMuPDF 作为文本块解析工具。

选择原因：

- 与 Phase 2 页面渲染使用同一套 PDF 页面对象和 `page.rect` 坐标系统。
- `page.get_text("blocks", sort=True)` 可直接返回文本块 bbox，坐标单位为 PDF point。
- bbox 可直接叠加到 Phase 2 的页面 PNG 上，无需额外坐标转换。
- 对 V0 来说足够轻量、可测、本地可运行。

### 4.2 后续备选

- `pdfplumber`：Phase 4 表格结构抽取时作为候选工具。
- OCR 引擎：V1 处理扫描件和图片型 PDF 时再接入。
- Layout model：V1/V2 用于复杂版面、图表和公式节点。

## 5. 数据模型设计

新增 `evidence_nodes` 表。

字段：

- `id`: UUID string，主键。
- `document_id`: 所属文档。
- `page_id`: 所属页面。
- `node_type`: 节点类型，Phase 3 固定为 `text_block`。
- `text`: 文本块内容。
- `bbox_json`: JSON string，格式为 `[x0, y0, x1, y1]`，单位为 PDF point。
- `reading_order`: 文档内阅读顺序，从 1 开始递增。
- `metadata_json`: JSON string，保存解析来源、PyMuPDF block 编号、行数等。
- `created_at`: 创建时间。

关系：

- `Document 1 -> N EvidenceNode`
- `Page 1 -> N EvidenceNode`

设计取舍：

- V0 使用 SQLite，bbox 与 metadata 先用 JSON string 存储，避免在早期引入数据库方言差异。
- EvidenceNode 作为统一证据节点表，而不是创建 `text_blocks` 专表，方便后续扩展 `table`, `figure`, `caption`, `section`。

## 6. 后端服务设计

新增 `backend/app/services/evidence.py`。

核心能力：

- `parse_document_text_blocks(db, document_id)`
  - 校验文档存在。
  - 校验 Phase 2 页面记录存在；没有页面记录时返回 `409 Conflict`。
  - 将文档状态置为 `parsing`。
  - 打开原始 PDF。
  - 逐页读取 `page.get_text("blocks", sort=True)`。
  - 仅保留文本块。
  - 删除该文档旧的 `text_block` 节点，重新写入新节点。
  - 成功后将文档状态置为 `parsed`。
- `list_document_text_blocks(db, document_id)`
  - 返回文档所有 `text_block` 节点。
- `list_page_text_blocks(db, document_id, page_number)`
  - 返回单页 `text_block` 节点。

错误处理：

- 未上传文档：`404 Document not found`。
- 未渲染页面：`409 Render pages before parsing text blocks`。
- 原始 PDF 缺失：`404 Original PDF file not found`。
- 解析失败：文档状态置为 `failed`，返回 `400 Text parsing failed`。

## 7. API 设计

新增接口：

```text
POST /api/documents/{document_id}/parse-text
GET  /api/documents/{document_id}/text-blocks
GET  /api/documents/{document_id}/pages/{page_number}/text-blocks
```

响应模型：

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "page_id": "uuid",
  "page_number": 1,
  "node_type": "text_block",
  "text": "example text",
  "bbox": [72.0, 70.2, 210.0, 84.8],
  "reading_order": 1,
  "metadata": {
    "source": "pymupdf",
    "block_no": 0,
    "line_count": 1
  },
  "created_at": "..."
}
```

## 8. 前端交互设计

前端新增：

- 文档卡片增加 `Parse text` 操作。
- `PageViewer` 加载第一页文本块。
- 页面图片上按 bbox 百分比绘制 overlay。
- 顶部展示文本块数量。
- 文本块 hover/title 可看到阅读顺序和文本摘要。

设计要求：

- 保持 Phase 2 的页面图像和尺寸信息。
- 文本块 overlay 使用 PDF point 坐标换算百分比：
  - `left = x0 / page.width`
  - `top = y0 / page.height`
  - `width = (x1 - x0) / page.width`
  - `height = (y1 - y0) / page.height`
- 不在前端做坐标修正，避免隐藏后端坐标问题。

## 9. 测试和验收标准

后端测试：

- 上传测试 PDF，渲染页面，解析文本块，返回非空 evidence nodes。
- 校验 `bbox`、`page_number`、`reading_order`、`node_type`。
- 校验单页文本块过滤。
- 未渲染直接解析时返回 `409`。
- 解析成功后文档状态为 `parsed`。

前端验证：

- `npm run build` 通过。
- 页面 viewer 可接受 `textBlocks` 并渲染 overlay。

视觉 smoke：

- 使用生成的测试 PDF 跑解析流程。
- 至少检查解析出的文本 bbox 与页面尺寸同坐标系，前端 overlay 不依赖测试 bbox。

## 10. 风险和取舍

- PyMuPDF 文本块对复杂多栏、脚注、页眉页脚的阅读顺序不一定完美。V0 接受该限制，后续通过版面模型和 reranker 改进。
- PDF 内嵌文本质量差时会出现乱码或缺字。OCR 留到后续版本。
- 只保存文本块，尚未建立图边。Phase 5/6 再建立检索工具和 Agent 使用方式。

## 11. 完成定义

- Phase 3 详细设计完成。
- 后端 `EvidenceNode` 模型、schema、service、API 完成。
- 前端文档操作和页面文本块 overlay 完成。
- 后端测试通过。
- 前端构建通过。
- README 和 Batch 1 工作日志更新。
