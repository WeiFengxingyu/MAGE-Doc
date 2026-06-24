# MAGE-Doc V0 Batch 1 工作日志

## 2026-06-23

### 当前阶段

Phase 0：项目骨架。

### 用户要求

- 延续 RepoLens 的开发方式。
- V0 的每一个小 Phase 先写详细设计文档。
- 按详细设计执行实现。
- 实现过程和对话用一份大阶段文档记录。
- 工作流本身也要记录成开发流程或标准。
- 从 Phase 0 开始开发。

### 已完成决策

- 新增 `docs/development-workflow.md` 作为项目开发流程标准。
- V0 详细设计文档放在 `docs/v0/`。
- V0 Batch 1 的过程记录统一写入 `docs/v0/batch1-worklog.md`。
- Phase 0 只做工程骨架，不提前实现 PDF 上传、解析和 Agent。

### Phase 0 设计摘要

Phase 0 将建立：

- FastAPI 后端。
- Next.js 前端。
- `.env.example`。
- Docker Compose 骨架。
- `/health` 和 `/api/status`。
- 前端工作台占位和后端健康状态。

### 实现记录

- 新增 `docs/development-workflow.md`，固化“每个小 Phase 先写详细设计，再实现、验证、记录”的流程。
- 新增 `docs/v0/phase00-project-skeleton-detailed-design.md`。
- 创建 FastAPI 后端骨架：
  - `backend/pyproject.toml`
  - `backend/app/main.py`
  - `backend/app/api/health.py`
  - `backend/app/core/config.py`
  - `backend/app/tests/test_health.py`
- 创建 Next.js 前端骨架：
  - `frontend/package.json`
  - `frontend/app/page.tsx`
  - `frontend/app/layout.tsx`
  - `frontend/app/globals.css`
  - `frontend/lib/api.ts`
  - `frontend/types/api.ts`
- 新增 `.env.example`、`.gitignore`、`docker-compose.yml`、前后端 Dockerfile。
- README 更新 Phase 0 快速启动和状态说明。

### 验证记录

- 后端测试通过：

```text
F:\Desktop\agent\RepoLens\backend\.venv\Scripts\python.exe -m pytest
2 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 注意：MAGE-Doc 自己的 `backend\.venv` 已创建，但由于当前网络访问 Python 包索引不稳定，后端依赖安装多次超时。Phase 0 验证临时复用 RepoLens 已验证的 Python 3.11 虚拟环境执行测试。项目自身的 `pyproject.toml` 已声明完整依赖，后续网络恢复后可执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### 遗留问题

- 后续 Phase 需要在 MAGE-Doc 自己的虚拟环境中完成依赖安装，避免长期复用 RepoLens 环境。
- Docker Compose 目前是骨架配置，尚未作为 Phase 0 验证项强制构建。

后续更新：Phase 1 已使用清华 PyPI 镜像完成 MAGE-Doc 本项目 `.venv` 依赖安装，后端验证已切回本项目虚拟环境。

### 下一步

进入 Phase 1：文档上传与状态管理。开始前先创建 `docs/v0/phase01-document-upload-detailed-design.md`。

## 2026-06-23 Phase 1

### 当前阶段

Phase 1：文档上传与状态管理。

### Phase 1 设计摘要

Phase 1 负责完成 PDF 上传、原始文件保存、document 元数据持久化、列表/详情/状态 API，以及前端上传面板和文档列表。

本阶段明确不做 PDF 页数解析、页面渲染、文本块解析和 Agent 问答。`page_count` 作为可空字段预留给 Phase 2。

### 实现记录

- 后端新增配置：
  - `MAGEDOC_DATABASE_URL`
  - `MAGEDOC_WORKSPACE_ROOT`
  - `MAGEDOC_UPLOAD_MAX_BYTES`
- 新增 SQLAlchemy 基础设施：
  - `backend/app/db/session.py`
  - `backend/app/db/init_db.py`
- 新增 document 数据模型和 schema：
  - `backend/app/models/document.py`
  - `backend/app/schemas/document.py`
- 新增 document service：
  - 校验 PDF 文件名。
  - 校验 content type。
  - 分块写入 `.magedoc/uploads/<document_id>/original.pdf`。
  - 保存文件大小、状态和元数据。
- 新增 document API：
  - `POST /api/documents`
  - `GET /api/documents`
  - `GET /api/documents/{document_id}`
  - `GET /api/documents/{document_id}/status`
- 上传协议取舍：
  - 保持标准 multipart/form-data 上传协议。
  - 已将 `python-multipart` 纳入 `pyproject.toml`。
  - 使用清华 PyPI 镜像将后端依赖安装到 MAGE-Doc 自己的 `.venv`。
  - 前端使用文件选择控件，Next.js server action 用 FormData 转发给 FastAPI。
- 前端新增：
  - `frontend/app/actions.ts`
  - `frontend/components/upload-form.tsx`
  - `frontend/components/document-list.tsx`
  - 文档上传表单、文档列表、状态 badge 和文件大小显示。
- 后端启动初始化改为 FastAPI lifespan，避免 `on_event` 弃用警告。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
7 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

### 遗留问题

- Phase 1 尚不解析 `page_count`，该字段保持 `null`，Phase 2 页面渲染阶段填充。
- 后端依赖已安装到 MAGE-Doc 自己的 `.venv`。后续继续使用本项目虚拟环境验证。

### 下一步

进入 Phase 2：页面渲染与坐标系统。开始前先创建 `docs/v0/phase02-page-rendering-coordinate-system-detailed-design.md`。

## 2026-06-23 Phase 2

### 当前阶段

Phase 2：页面渲染与坐标系统。

### Phase 2 设计摘要

Phase 2 使用 PyMuPDF 将已上传 PDF 渲染为页面 PNG，保存 PDF point 尺寸、PNG pixel 尺寸和图片路径，建立后续 bbox overlay 的坐标基础。

本阶段明确不做文本块解析、表格解析、OCR、图表检测和真实 evidence bbox。前端只展示测试 bbox overlay，用于验证坐标换算链路。

### 实现记录

- 工具选型确认：
  - Phase 2 主工具选择 PyMuPDF。
  - 选择原因是它同时支持页面渲染、`page.rect` 原始尺寸、PDF point 坐标体系和后续 block bbox 抽取。
  - Poppler 作为未来视觉 QA 备选，pdfplumber 留到 Phase 3/4 的文本/表格解析辅助。
- 后端新增依赖：
  - `pymupdf>=1.24.0`
- 新增页面模型和 schema：
  - `backend/app/models/page.py`
  - `backend/app/schemas/page.py`
- 新增页面渲染服务：
  - `backend/app/services/pages.py`
  - 使用 `page.get_pixmap(matrix=fitz.Matrix(render_zoom, render_zoom), alpha=False)` 渲染 PNG。
  - 保存 PDF point 尺寸、PNG pixel 尺寸、页面图片路径。
- 新增页面 API：
  - `POST /api/documents/{document_id}/render`
  - `GET /api/documents/{document_id}/pages`
  - `GET /api/documents/{document_id}/pages/{page_number}`
  - `GET /api/documents/{document_id}/pages/{page_number}/image`
- 更新配置：
  - `MAGEDOC_RENDER_ZOOM=2.0`
  - `.magedoc/page-images/<document_id>/page-0001.png`
- 前端新增：
  - `renderDocument`
  - `listPages`
  - `renderDocumentAction`
  - `PageViewer`
  - 文档卡片 `Render pages` 按钮。
  - 页面图片展示、PDF/PNG 尺寸展示和测试 bbox overlay。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
10 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 服务层视觉 smoke 通过：
  - 使用 PyMuPDF 生成 1 页测试 PDF。
  - 调用 `render_document_pages` 渲染 PNG。
  - 目视检查生成图片，页面文本清晰，非空白、非坏图。

### 遗留问题

- 本地 uvicorn 后台进程在当前执行环境中没有稳定保活，API 级 smoke 改用 TestClient 测试和服务层视觉 smoke 证明。
- Phase 2 只提供测试 bbox overlay。真实文本/表格/图表 bbox 从 Phase 3 开始接入。

### 下一步

进入 Phase 3：文本块解析。开始前先创建 `docs/v0/phase03-text-block-parsing-detailed-design.md`。

## 2026-06-24 Phase 3

### 当前阶段

Phase 3：文本块解析与证据节点。

### Phase 3 设计摘要

Phase 3 将 Phase 2 的页面坐标系统接入真实文本证据。系统使用 PyMuPDF 从已渲染 PDF 中提取文本块，将文本、bbox、页码、阅读顺序和解析元数据保存为 `text_block` evidence node，并在前端页面 viewer 上展示真实文本块 overlay。

### 关键决策

- 继续使用 PyMuPDF 作为文本块解析工具，保证文本 bbox 与页面渲染坐标同源。
- 新增统一 `evidence_nodes` 表，而不是临时 `text_blocks` 表，为后续表格、图片、标题、章节等多模态节点留出扩展空间。
- 解析动作要求文档先完成页面渲染；未渲染直接解析返回 `409 Conflict`。

### 实现记录

- 后端新增统一证据节点模型：
  - `backend/app/models/evidence.py`
  - `EvidenceNode` 支持 `document_id`、`page_id`、`node_type`、`text`、`bbox_json`、`reading_order`、`metadata_json`。
  - `Document` 与 `Page` 增加 `evidence_nodes` 关系。
- 后端新增 evidence schema 和 service：
  - `backend/app/schemas/evidence.py`
  - `backend/app/services/evidence.py`
  - `parse_document_text_blocks` 使用 PyMuPDF `page.get_text("blocks", sort=True)` 抽取文本块。
  - bbox 以 PDF point 坐标保存，和 Phase 2 页面尺寸同源。
  - 解析成功后文档状态更新为 `parsed`。
- 后端新增 API：
  - `POST /api/documents/{document_id}/parse-text`
  - `GET /api/documents/{document_id}/text-blocks`
  - `GET /api/documents/{document_id}/pages/{page_number}/text-blocks`
- 后端新增测试：
  - `backend/app/tests/test_evidence.py`
  - 覆盖渲染后解析、单页文本块过滤、未渲染直接解析返回 `409`。
- 前端新增：
  - `EvidenceNode` 类型。
  - `parseTextBlocks` 和 `listPageTextBlocks` API helper。
  - 文档卡片 `Parse text` 操作。
  - `PageViewer` 使用真实文本块 bbox overlay 替换 Phase 2 测试 bbox。
  - 页面状态更新为 Phase 3，当前范围显示为文本块证据 overlay。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
13 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 端到端 smoke 通过：
  - 生成 1 页测试 PDF。
  - 上传、渲染、解析文本块。
  - 返回 `document_status=parsed`。
  - 返回 2 个文本块节点。
  - 第一文本块 bbox 为 PDF point 坐标，例如 `[72.0, 78.175..., 222.413..., 93.289...]`。

### 遗留问题

- PyMuPDF 默认文本块阅读顺序对复杂多栏 PDF 可能不完美，后续需要 layout-aware rerank 或版面模型增强。
- 当前只解析内嵌文本，不处理扫描 PDF；OCR 留到后续版本。
- EvidenceNode 尚未建立图边，Phase 5/6 再接检索工具和 Agent。

### 下一步

进入 Phase 4：基础表格解析。开始前先创建 `docs/v0/phase04-table-parsing-detailed-design.md`。

## 2026-06-24 Phase 4

### 当前阶段

Phase 4：基础表格解析与表格证据节点。

### Phase 4 设计摘要

Phase 4 将 evidence node 从文本扩展到表格。系统使用 PyMuPDF `page.find_tables()` 检测规则线表格，提取表格整体 bbox、单元格 bbox、行列规模和二维文本矩阵，并保存为 `table` evidence node。

### 关键决策

- 使用 PyMuPDF `page.find_tables()` 作为 V0 主表格解析工具，保证表格 bbox 与页面渲染、文本块解析坐标同源。
- 继续复用 `evidence_nodes` 表，`node_type=table`，单元格和矩阵放入 metadata。
- V0 不做跨页表格合并、复杂表头推断和 OCR 表格识别。

### 实现记录

- 后端扩展 evidence service：
  - 新增 `TABLE_NODE_TYPE = "table"`。
  - 新增 `parse_document_tables`，使用 PyMuPDF `page.find_tables()` 抽取表格。
  - 保存表格整体 bbox、单元格 bbox、二维矩阵、行列规模和 TSV 文本摘要。
  - 解析成功后文档状态更新为 `tables_parsed`。
- 后端新增 API：
  - `POST /api/documents/{document_id}/parse-tables`
  - `GET /api/documents/{document_id}/tables`
  - `GET /api/documents/{document_id}/pages/{page_number}/tables`
- 后端新增测试：
  - `backend/app/tests/test_tables.py`
  - 使用 PyMuPDF 生成规则线表格 PDF。
  - 覆盖表格解析、单页表格过滤、未渲染直接解析返回 `409`。
- 前端新增：
  - `parseTables` 和 `listPageTables` API helper。
  - 文档卡片 `Parse tables` 操作。
  - `EvidenceNode.node_type` 支持 `text_block | table`。
  - `PageViewer` 同时展示文本块 overlay 和表格 overlay。
  - 页面状态更新为 Phase 4，当前范围显示为文本和表格证据 overlay。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
16 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 表格解析 smoke 通过：
  - 生成 1 页规则线表格 PDF。
  - 上传、渲染、解析表格。
  - 返回 `document_status=tables_parsed`。
  - 返回 1 个表格节点。
  - 表格 bbox 为 `[60.0, 80.0, 330.0, 164.0]`。
  - 表格形状为 `3x3`，第一行为 `["Metric", "2025", "2026"]`，cell count 为 9。

### 遗留问题

- PyMuPDF 提示可使用 `pymupdf_layout` 获得更强页面布局分析，后续版本可评估接入。
- V0 当前主要覆盖规则线表格；无边框表格、跨页表格、复杂表头和扫描表格留到后续增强。
- `document.status` 当前是单状态字段，文本解析和表格解析会相互覆盖最终状态；后续可拆为 pipeline step 状态。

### 下一步

进入 Phase 5：基础检索与工具层。开始前先创建 `docs/v0/phase05-retrieval-tools-detailed-design.md`。

## 2026-06-24 Phase 5

### 当前阶段

Phase 5：基础检索与工具层。

### Phase 5 设计摘要

Phase 5 在已有 `text_block` 和 `table` evidence nodes 上建立本地 BM25-style 检索，并抽象出可供 Phase 6 Agent 调用的工具接口：`search_evidence`、`inspect_page`、`read_table`、`verify_answer`。

### 关键决策

- V0 不接外部 embedding 服务，先用本地可解释 BM25-style keyword retrieval。
- 工具响应携带结构化 trace，但暂不持久化到数据库。
- 搜索结果内嵌 evidence node，保留 page、bbox、node_id 和 matched terms。
- Phase 5 不生成答案，答案生成和 Agent planning 留到 Phase 6。

### 实现记录

- 后端新增工具 schema：
  - `backend/app/schemas/tools.py`
  - `SearchResponse`
  - `InspectPageResponse`
  - `ReadTableResponse`
  - `VerifyAnswerRequest`
  - `VerifyAnswerResponse`
  - `ToolTraceResponse`
- 后端新增 retrieval service：
  - `backend/app/services/retrieval.py`
  - `search_evidence` 使用本地 BM25-style keyword retrieval。
  - `inspect_page_tool` 返回页面元数据和 evidence 概览。
  - `read_table_tool` 返回表格 matrix、cells、row/col count 和 bbox。
  - `verify_answer_tool` 校验 answer 是否非空、citation 是否存在且属于当前文档。
- 后端新增 API：
  - `GET /api/documents/{document_id}/search`
  - `GET /api/documents/{document_id}/tools/inspect-page/{page_number}`
  - `GET /api/documents/{document_id}/tools/read-table/{table_id}`
  - `POST /api/documents/{document_id}/tools/verify-answer`
- 后端新增测试：
  - `backend/app/tests/test_retrieval.py`
  - 覆盖文本检索、表格检索、页面检查、读表工具和答案引用校验。
- 前端新增：
  - `SearchResponse`、`SearchResult`、`ToolTrace`、`SearchState` 类型。
  - `searchEvidence` API helper。
  - `searchEvidenceAction` server action。
  - `RetrievalPanel` 检索调试面板。
  - 页面状态更新为 Phase 5，当前范围显示为 evidence retrieval tools。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
19 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 检索 smoke 通过：
  - 生成 1 页含正文和表格的 PDF。
  - 上传、渲染、解析文本、解析表格。
  - 搜索 `Revenue 2026`。
  - 返回 3 个结果。
  - top result 为 `table`，page=1，matched terms 为 `["revenue", "2026"]`。
  - top bbox 为 `[60.0, 95.0, 330.0, 179.0]`。
  - trace 为 `tool_name=search_evidence`，`output_summary=3 results`。

### 遗留问题

- BM25-style 检索不具备语义泛化能力，V1 需要接入 embedding + reranker。
- 工具 trace 当前随响应返回，尚未持久化到 `tool_calls` 表。
- 中文检索采用 ASCII token + CJK char/bigram 的轻量策略，后续可接入更强分词或多语种 embedding。
- 前端检索结果暂不联动页面高亮，点击 citation 跳转与高亮留到 Phase 7。

### 下一步

进入 Phase 6：V0 Agentic RAG 闭环。开始前先创建 `docs/v0/phase06-agentic-rag-loop-detailed-design.md`。

## 2026-06-24 Phase 6

### 当前阶段

Phase 6：V0 Agentic RAG 闭环。

### Phase 6 设计摘要

Phase 6 在 Phase 5 的工具层之上实现一个确定性 V0 Agent workflow。系统对问题做轻量分类，按计划调用 `search_evidence`、`inspect_page`、`read_table`、`verify_answer`，输出 answer、citations 和 trace。

### 关键决策

- V0 不调用外部 LLM，先用确定性 workflow agent 保证本地可运行和可测试。
- 表格型问题优先 table evidence，文本型问题优先 text_block evidence。
- 引用校验必须调用 Phase 5 的 `verify_answer`。
- Phase 6 不做 citation 点击跳转和高亮联动，留到 Phase 7。

### 实现记录

- 后端新增 Agent schema：
  - `backend/app/schemas/agent.py`
  - `QuestionRequest`
  - `CitationResponse`
  - `QuestionAnswerResponse`
- 后端新增 Agent workflow service：
  - `backend/app/services/agent.py`
  - 规则分类 `table_lookup` / `text_lookup`。
  - 表格问题调用 `search_evidence -> read_table -> verify_answer`。
  - 文本问题调用 `search_evidence -> inspect_page -> verify_answer`。
  - 无结果时返回空 citation，并通过 verify 标记不通过。
- 后端新增 API：
  - `POST /api/documents/{document_id}/questions`
- 后端新增测试：
  - `backend/app/tests/test_agent.py`
  - 覆盖表格问题、文本问题、空问题和无证据问题。
- 前端新增：
  - `QuestionAnswerResponse`、`Citation`、`Verification`、`AskState` 类型。
  - `askQuestion` API helper。
  - `askQuestionAction` server action。
  - `AskPanel` 问答面板，展示 answer、citations、trace 和 verification 状态。
  - 页面状态更新为 Phase 6，当前范围显示为 Agentic RAG answer with citations。

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
23 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- Agent smoke 通过：
  - 生成 1 页含正文和表格的 PDF。
  - 上传、渲染、解析文本、解析表格。
  - 提问 `What was revenue in 2026?`
  - 返回 `question_type=table_lookup`。
  - answer 为 `Based on table evidence on page 1, the most relevant row is: Revenue | 100 | 128.`
  - citation count 为 1，citation type 为 `table`。
  - trace tools 为 `["search_evidence", "read_table", "verify_answer"]`。
  - verification passed 为 `True`。

### 遗留问题

- V0 Agent 使用确定性模板答案，不调用 LLM，语言表达能力有限。
- 问题分类和表格行选择是规则型，复杂问题需要 Phase 7/V1 的 planner 和 generator 增强。
- 当前 question 和 tool trace 未持久化到数据库，后续可引入 `questions` 和 `tool_calls` 表。
- 前端 citation 点击跳转、高亮 evidence bbox 留到 Phase 7。

### 下一步

进入 Phase 7：前端问答与引用高亮。开始前先创建 `docs/v0/phase07-qa-citation-highlight-detailed-design.md`。

## 2026-06-24 Phase 7

### 当前阶段

Phase 7：前端问答与引用高亮。

### Phase 7 设计摘要

Phase 7 将 Phase 6 的 answer/citations 结果升级为可交互证据定位体验。用户点击 Ask 面板中的 citation 后，PageViewer 自动切换到 citation 所在页，并用高亮 bbox 标出证据位置。

### 关键决策

- Phase 7 不新增后端 Agent 能力，聚焦前端引用定位闭环。
- 新增 client-side `DocumentWorkbench` 管理 selected citation 状态。
- `PageViewer` 升级为 client component，支持 citation page 切换和 bbox highlight。
- 只支持单 citation 高亮，多 citation 联动留到后续版本。

### 实现记录

- 前端新增 `DocumentWorkbench`：
  - `frontend/components/document-workbench.tsx`
  - 管理 `selectedCitation` client state。
  - 组合 `PageViewer`、`AskPanel` 和 `RetrievalPanel`。
- `AskPanel` citation 交互增强：
  - citation item 改为可点击 button。
  - 点击后调用 `onCitationSelect`。
  - 当前 citation 增加 active 样式。
- `PageViewer` 升级为 client component：
  - 接收 `selectedCitation`。
  - 根据 citation page number 切换 active page。
  - 按 active page 动态加载 text blocks 和 tables。
  - 使用 citation bbox 绘制 selected citation highlight。
- 首页组合方式调整：
  - `DocumentWorkbenchAsync` 在 server 侧加载 active document、pages、第一页 evidence。
  - client 侧接管 Ask/Page/Retrieval 的交互联动。
- 样式新增：
  - `.citation-button`
  - `.citation-button-active`
  - `.selected-citation-banner`
  - `.selected-citation-bbox`

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
23 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- 交互路径 smoke 通过：
  - `AskPanel` citation button 调用 `onCitationSelect`。
  - `DocumentWorkbench` 持有 `selectedCitation` 并传递给 `PageViewer`。
  - `PageViewer` 根据 `selectedCitation.page_number` 调用 `setActivePageNumber`。
  - `PageViewer` 使用 `selectedCitation.bbox` 绘制 `.selected-citation-bbox`。

### 遗留问题

- 当前仅支持单 citation 高亮，多 citation 同时高亮留到后续版本。
- citation 选中状态只在前端内存中维护，不持久化也不进入 URL。
- 目前没有完整翻页控件，只通过 citation 驱动页面切换。
- 前端未做 Playwright 浏览器截图验证，当前以 TypeScript build 和代码路径 smoke 作为 Phase 7 验证。

### 下一步

V0 Batch 1 的核心演示链路已形成。下一步可进入 Phase 8/V0 polish，或进入 Batch 2：Evidence Graph V1。

## 2026-06-24 Phase 8

### 当前阶段

Phase 8：V0 Demo Polish 与一键准备。

### Phase 8 设计摘要

Phase 8 将 V0 的多步骤演示整理成更顺滑的 demo workflow。用户上传 PDF 后点击 `Prepare demo`，系统串行完成页面渲染、文本块解析和表格解析，然后进入 `demo_ready` 状态，可直接提问、查看 citation、点击 citation 高亮页面 bbox。

### 关键决策

- 新增同步 `prepare-demo` API，不引入后台队列。
- `Prepare demo` 会重新执行 render/text parse/table parse，保证 demo 状态稳定。
- 文档状态新增 `preparing_demo` 和 `demo_ready`。
- 新增 V0 demo runbook，方便简历展示和面试演示。

### 实现记录

- 后端新增 pipeline schema：
  - `backend/app/schemas/pipeline.py`
  - `PrepareDemoResponse`
  - `PipelineStepResponse`
- 后端新增 pipeline service：
  - `backend/app/services/pipeline.py`
  - `prepare_document_demo` 串行调用 render、parse text、parse tables。
  - 成功后设置 document status 为 `demo_ready`。
- 后端新增 API：
  - `POST /api/documents/{document_id}/prepare-demo`
- 后端新增测试：
  - `backend/app/tests/test_pipeline.py`
  - 覆盖 prepare-demo、状态更新、counts 返回，以及 prepare 后直接 ask。
- 前端新增：
  - `PrepareDemoResponse` 类型。
  - `prepareDemo` API helper。
  - `prepareDemoAction` server action。
  - 文档卡片 `Prepare demo` 主按钮。
  - `demo_ready` 和 `preparing_demo` 状态样式。
  - `DocumentWorkbench` demo ready 提示面板。
  - 页面状态更新为 Phase 8，当前范围显示为 V0 demo ready workflow。
- 文档新增：
  - `docs/v0/phase08-v0-demo-polish-detailed-design.md`
  - `docs/v0/v0-demo-runbook.md`

### 验证记录

- 后端测试通过：

```text
.venv\Scripts\python.exe -m pytest
24 passed, 1 warning
```

- 前端构建通过：

```text
npm run build
Compiled successfully
```

- Phase 8 smoke 通过：
  - 生成 1 页含正文和表格的 PDF。
  - 上传后只调用 `prepare-demo`。
  - 返回 `prepare_status=demo_ready`。
  - counts 为 `[1, 4, 1]`，对应 page/text/table。
  - steps 为 `["render_pages", "parse_text_blocks", "parse_tables"]`。
  - prepare 后直接提问 `What was revenue in 2026?`。
  - answer 包含 `Revenue | 100 | 128`。
  - citation count 为 1，verification passed 为 `True`。

### 遗留问题

- `prepare-demo` 是同步请求，大 PDF 会阻塞请求；后续可升级为后台 job。
- prepare 会覆盖旧页面/evidence，V0 接受以保证 demo 稳定。
- V0 demo runbook 仍依赖用户自己提供合适 PDF，后续可添加样例 PDF 或生成脚本。

### 下一步

提交并推送 GitHub。V0 Batch 1 已形成可演示闭环，下一步建议进入 Batch 2：Evidence Graph V1。
