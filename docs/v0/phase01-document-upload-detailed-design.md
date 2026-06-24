# Phase 1 详细设计：文档上传与状态管理

## 1. Phase 目标

Phase 1 的目标是完成 MAGE-Doc 的 PDF 文档上传、原始文件保存、元数据持久化、文档列表、详情和状态查询。

本阶段完成后，用户可以：

1. 在前端上传 PDF。
2. 后端校验文件类型并保存原始 PDF。
3. 系统创建 document 记录。
4. 前端展示文档列表、大小、状态和上传时间。
5. 用户可以查看单个文档详情和状态。

## 2. 非目标

本阶段不实现：

- PDF 页面渲染。
- PDF 页数解析。
- 文本块解析。
- 表格解析。
- bbox 坐标。
- Agentic RAG 问答。
- 检索和证据图。

`page_count` 在本阶段作为可空字段预留，Phase 2 页面渲染与坐标系统阶段再填充。

## 3. 用户可见结果

前端工作台从 Phase 0 的空状态升级为：

- 上传 PDF 的控件。
- 文档列表。
- 文档状态说明。
- 最近上传文档的元数据。
- 上传错误提示。

## 4. 后端设计

### 4.1 存储目录

默认 workspace：

```text
.magedoc/
  magedoc.sqlite
  uploads/
    <document_id>/
      original.pdf
```

配置项：

- `MAGEDOC_DATABASE_URL`
- `MAGEDOC_WORKSPACE_ROOT`
- `MAGEDOC_UPLOAD_MAX_BYTES`

### 4.2 数据模型

`documents`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | UUID |
| `filename` | string | 原始文件名 |
| `stored_filename` | string | 存储文件名，Phase 1 固定为 `original.pdf` |
| `file_path` | string | 原始 PDF 文件路径 |
| `content_type` | string | 上传 Content-Type |
| `file_size` | int | 字节数 |
| `page_count` | int nullable | Phase 2 填充 |
| `status` | string | `uploaded` / `failed` |
| `error_message` | string nullable | 错误信息 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 4.3 API

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/documents` | 使用标准 multipart/form-data 上传 PDF 并创建记录 |
| `GET` | `/api/documents` | 文档列表 |
| `GET` | `/api/documents/{document_id}` | 文档详情 |
| `GET` | `/api/documents/{document_id}/status` | 文档状态 |

### 4.4 上传协议与校验

Phase 1 使用标准 multipart/form-data 上传：

- 表单字段：`file`。
- FastAPI 类型：`UploadFile = File(...)`。
- 后端依赖：`python-multipart`。
- 前端使用文件选择控件，Next.js server action 负责把用户选择的 `File` 以 FormData 转发给后端。

必须校验：

- 文件名不能为空。
- 扩展名必须为 `.pdf`。
- Content-Type 允许：
  - `application/pdf`
  - `application/octet-stream`
  - 空值
- 文件大小必须大于 0。
- 文件大小不得超过 `MAGEDOC_UPLOAD_MAX_BYTES`。

Content-Type 不能作为唯一依据，因为部分浏览器或测试工具可能上传 `application/octet-stream`。

### 4.5 错误处理

- 非 PDF：`400`
- 空文件：`400`
- 超过大小限制：`413`
- 文档不存在：`404`
- 文件保存失败：`500`

## 5. 前端设计

### 5.1 UI 变化

首页仍保持工作台风格，新增：

- 上传面板。
- 上传按钮和文件名显示。
- 文档列表。
- 文档状态徽标。
- 文档元数据：文件大小、页数占位、上传时间。
- 上传错误提示。

### 5.2 前端 API

新增：

- `listDocuments()`
- `uploadDocument(file)`
- `getDocument(id)`
- `getDocumentStatus(id)`

类型：

```ts
type DocumentRecord = {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  page_count: number | null;
  status: "uploaded" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
};
```

## 6. 测试计划

后端测试：

- 上传有效 PDF。
- 列表返回上传文档。
- 详情接口返回文档。
- 状态接口返回文档状态。
- 拒绝非 PDF。
- 拒绝空 PDF。
- 不存在文档返回 404。

前端验证：

- TypeScript 构建通过。
- 页面能编译上传表单和文档列表。

## 7. 验收标准

- 后端测试全部通过。
- 前端 `npm run build` 通过。
- README 更新 Phase 1 状态。
- Batch 1 worklog 记录设计、实现和验证结果。

## 8. 风险与取舍

| 风险 | 取舍 |
| --- | --- |
| 上传接口引入 multipart 依赖 | 已将 `python-multipart` 纳入后端依赖，保持标准上传协议 |
| 过早解析页数导致范围膨胀 | `page_count` 本阶段保持 nullable |
| 文件名安全问题 | 后端不使用原始文件名作为存储名，仅保存为元数据 |
| 大文件占用内存 | Phase 1 使用分块读取并限制最大字节数 |
