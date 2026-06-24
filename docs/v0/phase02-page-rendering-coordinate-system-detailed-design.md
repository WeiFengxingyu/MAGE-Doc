# Phase 2 详细设计：页面渲染与坐标系统

## 1. Phase 目标

Phase 2 的目标是将已上传 PDF 渲染为页面图片，并建立稳定的 PDF 坐标系统，为后续文本块 bbox、表格 bbox、引用高亮和页面检查工具打基础。

本阶段完成后，用户可以：

1. 对已上传文档触发页面渲染。
2. 后端读取 PDF 页数，并更新 `documents.page_count`。
3. 后端保存每页 PNG 图片。
4. 后端保存每页 PDF 原始尺寸和渲染图片尺寸。
5. 前端展示页面导航、页面图片、页面元数据和测试 bbox overlay。

## 2. 非目标

本阶段不实现：

- 文本块解析。
- 表格解析。
- OCR。
- 图表检测。
- Agentic RAG。
- 真实 evidence bbox 高亮。

本阶段只提供页面级坐标基础和一个测试 bbox overlay，真实证据节点从 Phase 3 开始接入。

## 3. 坐标系统设计

MAGE-Doc 统一保存两套坐标：

| 坐标 | 来源 | 用途 |
| --- | --- | --- |
| PDF point 坐标 | PyMuPDF 页面坐标，单位 point | 后端 evidence bbox、表格 bbox、图节点 bbox |
| Image pixel 坐标 | PNG 渲染后的像素宽高 | 前端显示、截图和调试 |

后端 `pages` 表保存：

- `width`：PDF page width，point。
- `height`：PDF page height，point。
- `image_width`：PNG width，pixel。
- `image_height`：PNG height，pixel。

前端 overlay 换算：

```text
left = bbox.x0 / page.width * renderedImageClientWidth
top = bbox.y0 / page.height * renderedImageClientHeight
width = (bbox.x1 - bbox.x0) / page.width * renderedImageClientWidth
height = (bbox.y1 - bbox.y0) / page.height * renderedImageClientHeight
```

Phase 2 的测试 bbox：

```json
[72, 72, 240, 160]
```

它用于验证 overlay 缩放逻辑，不代表真实证据。

## 4. 后端设计

### 4.1 新增依赖

使用 PyMuPDF：

```text
pymupdf>=1.24.0
```

理由：

- 可读取 PDF 页数。
- 可获取页面原始尺寸。
- 可将页面稳定渲染为 PNG。
- 坐标系统和后续文本/表格 bbox 基础一致。

### 4.1.1 工具选型说明

Phase 2 的核心任务是“页面渲染 + 坐标系统”，不是单纯抽文本。因此主工具必须同时满足：

- 能读取页数和页面原始尺寸。
- 能将页面渲染为图片。
- 能保留 PDF point 坐标体系。
- 后续可继续用于文本块、图片块、bbox 和 page object 检查。
- 在 Windows、本地开发和 Docker 中都容易安装。

候选对比：

| 工具 | 优点 | 不适合作为 Phase 2 主工具的原因 | 决策 |
| --- | --- | --- | --- |
| PyMuPDF | Python 原生包；可获取 `page.rect`；可用 `page.get_pixmap()` 渲染；支持 Matrix/DPI；后续可抽 text/image block bbox | 依赖体积比纯解析库大，但这是渲染能力的合理成本 | 主工具 |
| Poppler / `pdftoppm` | 渲染质量成熟，CLI 稳定 | 需要系统二进制，Windows 和 Docker 额外安装成本高；坐标元数据还需另一个库配合 | 作为未来视觉 QA 可选工具 |
| pdfplumber | 文本、字符、线条、表格调试友好 | 不适合作为页面 PNG 渲染主链路 | Phase 3/4 可作为抽取辅助 |
| pypdf | 轻量，适合元数据和文本读取 | 不负责页面渲染 | 不用于 Phase 2 主链路 |
| pypdfium2 | 渲染能力强 | 后续 text/table/layout 坐标生态不如 PyMuPDF 统一 | 备选 |

最终选择：

> Phase 2 使用 PyMuPDF 作为主渲染和坐标工具；Phase 3/4 如需要更强表格抽取，再引入 pdfplumber 作为辅助解析工具。

参考依据：

- PyMuPDF 官方文档提供 `Page.get_pixmap()` 页面渲染能力，并支持 Matrix/DPI 控制分辨率。
- PyMuPDF `page.rect` 与后续 text/image block bbox 坐标体系保持一致。

### 4.2 存储目录

```text
.magedoc/
  uploads/
    <document_id>/
      original.pdf
  page-images/
    <document_id>/
      page-0001.png
      page-0002.png
```

### 4.3 数据模型

新增 `pages` 表：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | UUID |
| `document_id` | string | 文档 ID |
| `page_number` | int | 1-based 页码 |
| `width` | float | PDF width，point |
| `height` | float | PDF height，point |
| `image_width` | int | PNG width，pixel |
| `image_height` | int | PNG height，pixel |
| `image_path` | string | PNG 本地路径 |
| `created_at` | datetime | 创建时间 |

唯一约束：

```text
document_id + page_number
```

### 4.4 状态流转

文档状态：

```text
uploaded -> rendering -> rendered
uploaded -> rendering -> failed
```

Phase 1 已有 `uploaded` / `failed`，Phase 2 增加 `rendering` / `rendered`。

### 4.5 API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/documents/{id}/render` | 渲染 PDF 页面，返回页面摘要 |
| `GET` | `/api/documents/{id}/pages` | 获取文档页面列表 |
| `GET` | `/api/documents/{id}/pages/{page_number}` | 获取单页元数据 |
| `GET` | `/api/documents/{id}/pages/{page_number}/image` | 返回页面 PNG |

### 4.6 渲染参数

P0 默认：

- `zoom = 2.0`
- `matrix = fitz.Matrix(zoom, zoom)`
- PNG 输出。

这样常见 A4 页面宽度约为 1190px，足够用于前端查看和 bbox 调试。

## 5. 前端设计

### 5.1 UI 变化

在文档工作台中增加：

- 文档列表中的 `Render pages` 按钮。
- 当前文档页面列表。
- 页面导航。
- 页面图片查看器。
- 页面元数据：PDF size、image size、page number。
- 测试 bbox overlay 开关或默认展示。

### 5.2 前端 API

新增：

- `renderDocument(documentId)`
- `listPages(documentId)`
- `getPage(documentId, pageNumber)`

新增类型：

```ts
type PageRecord = {
  id: string;
  document_id: string;
  page_number: number;
  width: number;
  height: number;
  image_width: number;
  image_height: number;
  image_url: string;
  created_at: string;
};
```

## 6. 测试计划

后端测试：

- 上传 PDF 后调用 render，生成页面记录和 PNG 文件。
- render 更新 document `page_count` 和 `status=rendered`。
- 页面列表按页码排序。
- 单页详情返回 image URL。
- 页面图片接口返回 PNG。
- 不存在文档返回 404。
- 非法页码返回 404。

测试 PDF：

- 使用 PyMuPDF 在测试中生成一个 2 页临时 PDF，避免依赖外部文件。

前端验证：

- `npm run build` 通过。
- TypeScript 能编译页面查看器、render action 和 PageRecord 类型。

## 7. 验收标准

- 后端测试全部通过。
- 前端构建通过。
- 上传 PDF 后能渲染页面，并返回页数。
- 前端能显示页面图片和测试 bbox overlay。
- README 和 worklog 更新 Phase 2 状态。

## 8. 风险与取舍

| 风险 | 取舍 |
| --- | --- |
| PyMuPDF 依赖体积较大 | Phase 2 是页面渲染核心能力，必须安装 |
| 渲染大 PDF 较慢 | P0 同步渲染，V1 再改异步任务 |
| 重复渲染覆盖图片 | Phase 2 允许幂等重渲染，先删除旧页面记录再写新记录 |
| 前端 overlay 和图片缩放不一致 | 使用 PDF point 比例换算，保留 image metadata 便于调试 |
