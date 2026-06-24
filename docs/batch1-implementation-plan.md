# MAGE-Doc 第一批实现计划：V0 Foundation

## 1. 批次目标

第一批实现目标是完成 MAGE-Doc 的最小可演示基础：

> 上传 PDF -> 渲染页面 -> 解析文本/表格/图片区域 -> 保存 bbox -> 建立基础检索 -> 通过工具式问答返回带引用答案 -> 前端高亮证据。

这一批不追求完整多模态智能体，但必须把后续 V1 的地基打稳。

## 2. 交付范围

### 2.1 后端

- FastAPI 项目骨架。
- SQLite 元数据存储。
- 文档上传 API。
- 文档状态 API。
- PDF 页面渲染服务。
- PDF layout parser。
- 基础 table parser。
- figure region detector 占位实现。
- evidence node 数据模型。
- 基础 BM25 检索。
- 工具 API：
  - `search_text`
  - `inspect_page`
  - `read_table`
  - `verify_answer`
- 简化 Agentic RAG 服务。

### 2.2 前端

- Next.js 项目骨架。
- 文档上传区。
- 文档列表。
- PDF 页面查看器。
- bbox 高亮层。
- Ask 面板。
- 答案引用列表。
- 基础 trace 面板。

### 2.3 文档

- README 快速启动。
- `.env.example`。
- V0 demo runbook。
- P0 数据模型说明。

## 3. 阶段拆分

### Phase 1：项目骨架

目标：

- 建立可运行的前后端基础。

任务：

- 创建 `backend` FastAPI 项目。
- 创建 `frontend` Next.js 项目。
- 创建 `docker-compose.yml`。
- 创建 `.env.example`。
- 后端提供 `/health`。
- 前端提供基础工作台页面。

验收：

- `uvicorn app.main:app --reload` 可启动。
- `npm run dev` 可启动。
- 前端能调用后端 `/health`。

### Phase 2：文档上传与状态管理

目标：

- 能上传 PDF，并在系统中记录文档。

任务：

- 设计 `documents` 表。
- 实现 `POST /api/documents`。
- 实现 `GET /api/documents`。
- 实现 `GET /api/documents/{document_id}`。
- 保存原始 PDF 到本地 workspace。
- 记录文档状态：uploaded / parsing / indexed / failed。
- 前端实现上传和文档列表。

验收：

- 用户上传 PDF 后文档出现在列表中。
- 后端能返回文档页数、大小、状态。
- 非 PDF 文件被拒绝。

### Phase 3：页面渲染与坐标系统

目标：

- 将 PDF 页面渲染为图片，并建立稳定坐标系统。

任务：

- 使用 PyMuPDF 渲染页面。
- 保存页面图片。
- 设计 `pages` 表。
- 记录 page width、height、image path。
- 实现 `GET /api/documents/{id}/pages/{page_number}`。
- 前端显示页面图片。
- 前端实现 bbox overlay 组件。

验收：

- 任意页面能在前端打开。
- 后端返回页面尺寸和图片 URL。
- 前端能绘制测试 bbox，并准确覆盖页面区域。

### Phase 4：文本块解析

目标：

- 从 PDF 中提取文本块、bbox 和阅读顺序。

任务：

- 使用 PyMuPDF 或 pdfplumber 提取文本块。
- 设计 `evidence_nodes` 表。
- 保存 `text_block` 节点。
- 记录 page_number、bbox、text、reading_order、confidence。
- 简单识别标题候选。
- 过滤页眉页脚候选。
- 前端 debug overlay 显示文本块边框。

验收：

- 文档解析后能看到页面上的文本块高亮。
- 点击文本块能显示文本内容。
- 文本块坐标和页面渲染坐标一致。

### Phase 5：基础表格解析

目标：

- 解析单页表格，并让表格成为独立证据。

任务：

- 使用 pdfplumber 提取表格候选。
- 设计 table metadata。
- 保存 `table`、`table_row`、`table_cell` 节点。
- 保存 table bbox 和 cell text。
- 生成表格 markdown summary。
- 实现 `read_table` 工具。
- 前端显示表格结构视图。

验收：

- 年报 PDF 中至少能解析出主要财务表格。
- `read_table(table_id)` 返回行列和单元格。
- 表格 bbox 可以在页面上高亮。

### Phase 6：基础检索与工具层

目标：

- 让文本和表格可以被工具召回。

任务：

- 实现 BM25 或轻量关键词检索。
- 为 text block 建立索引。
- 为 table summary 建立索引。
- 实现 `search_text`。
- 实现 `inspect_page`。
- 实现 `verify_answer` 的基础规则。
- 记录 tool call trace。

验收：

- 输入关键词能召回相关段落。
- 输入指标名能召回相关表格。
- 工具调用记录包含工具名、输入、输出摘要、耗时。

### Phase 7：V0 Agentic RAG 闭环

目标：

- 形成最小 Agentic RAG 问答。

任务：

- Question classifier 简化实现。
- Planner 简化实现。
- 根据问题选择 `search_text` 或 `search_tables`。
- 对召回证据执行 `inspect_page` 或 `read_table`。
- 生成答案。
- `verify_answer` 检查引用是否存在。
- 输出 answer、citations、trace。

验收：

- 文本问题返回文本引用。
- 表格问题返回表格引用。
- 答案引用包含 page、bbox、node_id。
- trace 能展示检索和读证据过程。

### Phase 8：前端问答与引用高亮

目标：

- 完成 V0 可演示工作台。

任务：

- Ask 面板。
- 答案区。
- 引用列表。
- 点击引用跳转页面。
- 高亮对应 bbox。
- Trace 面板显示工具调用。
- 空状态和错误状态。

验收：

- 完成一条端到端 Demo：
  1. 上传 PDF。
  2. 等待解析。
  3. 提问。
  4. 查看答案。
  5. 点击引用。
  6. PDF 页面高亮证据。
  7. 查看 trace。

## 4. 第一批技术选型

| 模块 | V0 选型 | 原因 |
| --- | --- | --- |
| Backend | FastAPI | 快速搭 API，和已有经验一致 |
| Metadata | SQLite + SQLAlchemy | P0 足够，便于本地部署 |
| PDF render | PyMuPDF | 页面渲染和 bbox 支持稳定 |
| Text extraction | PyMuPDF first, pdfplumber fallback | 降低解析复杂度 |
| Table extraction | pdfplumber | P0 先支持基础单页表格 |
| Retrieval | BM25 / keyword first | 第一批先不被 embedding 配置卡住 |
| Agent | 自定义 workflow first | V0 先简单可控，V1 再 LangGraph 化 |
| Frontend | Next.js + TypeScript | 适合做工作台 |

## 5. 数据模型草案

### 5.1 documents

```text
id
filename
file_path
page_count
status
error_message
created_at
updated_at
```

### 5.2 pages

```text
id
document_id
page_number
width
height
image_path
created_at
```

### 5.3 evidence_nodes

```text
id
document_id
page_id
node_type
text
bbox_json
reading_order
metadata_json
created_at
```

### 5.4 questions

```text
id
document_id
question
answer
status
created_at
```

### 5.5 tool_calls

```text
id
question_id
tool_name
input_json
output_summary
latency_ms
status
created_at
```

## 6. API 草案

| Method | Path | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/documents` | 上传 PDF |
| `GET` | `/api/documents` | 文档列表 |
| `GET` | `/api/documents/{id}` | 文档详情 |
| `POST` | `/api/documents/{id}/parse` | 解析文档 |
| `GET` | `/api/documents/{id}/pages/{page_number}` | 页面详情 |
| `POST` | `/api/documents/{id}/questions` | 提问 |
| `GET` | `/api/questions/{id}` | 答案详情 |
| `GET` | `/api/questions/{id}/trace` | trace |

## 7. Demo 验收问题

第一批至少准备 5 个问题：

1. “这份文档的主营业务收入是多少？”
2. “哪一页解释了毛利率变化原因？”
3. “2024 年研发费用是多少？请引用表格。”
4. “现金流相关风险在哪里提到？”
5. “这个指标在正文解释和表格数字是否一致？”

V0 不要求全部回答完美，但必须能展示：

- 检索证据。
- 读取页面或表格。
- 引用页码和 bbox。
- trace 可见。

## 8. 不做清单

第一批明确不做：

- 不做复杂 OCR。
- 不做完整图表视觉理解。
- 不做多文档集合。
- 不做权限系统。
- 不做完整 benchmark。
- 不做 MCP。
- 不做跨页表格合并。

这些都放到 V1/V2，避免第一批范围失控。

## 9. 第一批完成后的下一步

第一批完成后进入：

> Batch 2：Evidence Graph V1

Batch 2 会把 V0 的 evidence nodes 升级成完整 evidence graph：

- section node。
- table/figure/caption relation。
- nearby/next_block/caption_of edges。
- graph expansion tool。
- evidence path visualization。

