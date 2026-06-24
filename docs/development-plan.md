# MAGE-Doc 开发计划

## 1. 开发原则

MAGE-Doc 的开发目标不是堆功能，而是尽快形成一个面试可演示、技术可展开、指标可验证的闭环。

优先级：

1. **证据可定位**：任何答案都能跳转到 PDF 页和 bbox。
2. **表格可计算**：表格不是文本片段，而是结构化证据。
3. **Agent 可追踪**：能看到每一步为什么检索、读表、扩展证据和验证。
4. **评测可量化**：至少能证明 evidence graph agent 比 text-only RAG 更可靠。
5. **Demo 可讲清楚**：选择少量高质量长 PDF，打磨 5 到 8 个复杂问题。

## 2. P0 目标

P0 完成后应能演示：

1. 上传一份长 PDF。
2. 系统解析页面、文本块、表格和图片区域。
3. 系统构建证据图和索引。
4. 用户提出跨页/表格/图表相关问题。
5. Agent 通过工具多轮检索、读页、读表、扩展证据。
6. 最终答案带引用，点击引用能跳转 PDF 高亮区域。
7. Trace 面板展示 Planner、工具调用、Verifier 和证据路径。
8. 评测面板展示不同 RAG 策略对比。

## 3. Phase 划分

### Phase 0：项目骨架

产出：

- `backend` FastAPI 项目。
- `frontend` Next.js 项目。
- `docker-compose.yml`。
- `.env.example`。
- 基础 README。

验收：

- 后端 `/health` 可访问。
- 前端首页可访问。
- Docker Compose 能启动基础服务。

### Phase 1：PDF 导入与页面渲染

产出：

- PDF 上传 API。
- 文档列表和文档状态。
- 页面渲染为图片。
- 页面元数据保存。
- 前端 PDF 页面浏览器。

验收：

- 上传 PDF 后能看到页数和解析状态。
- 能在前端浏览页面图片。
- 页面坐标系统稳定，为后续 bbox 高亮做准备。

### Phase 2：Layout / Table / Figure 解析

产出：

- 文本块解析：text、bbox、page、reading order。
- 标题/章节候选识别。
- 表格解析：table、row、cell、caption 候选。
- 图片/图表区域候选。
- 页眉页脚候选过滤。

验收：

- 至少 3 份 PDF 能解析出可用文本块。
- 至少 1 份年报能解析出主要财务表格。
- 前端能显示 block/table/figure 边框调试视图。

### Phase 3：Evidence Graph 与索引

产出：

- EvidenceNode / EvidenceEdge 数据模型。
- document/page/section/block/table/cell/figure/caption 节点。
- contains/next_block/nearby/caption_of/mentions 边。
- BM25 索引。
- 向量索引适配器。
- 表格/指标索引。

验收：

- 给定页面或节点能查询邻域。
- 给定指标名能召回相关表格。
- 给定文本问题能召回相关文本块。
- Evidence graph API 返回可视化所需节点和边。

### Phase 4：Agentic RAG 工具层

产出：

- Tool registry。
- `search_text`。
- `search_tables`。
- `inspect_page`。
- `read_table`。
- `inspect_figure`。
- `expand_evidence_graph`。
- `calculate_metric`。
- `verify_answer`。
- tool call audit。

验收：

- 每个工具有结构化输入输出。
- 工具调用被记录到 trace。
- `read_table` 返回可复现计算的单元格结构。
- `verify_answer` 能标记 unsupported claim。

### Phase 5：Agent 编排闭环

产出：

- Question Classifier。
- Planner。
- Router。
- Evidence Collector。
- Evidence Graph Expander。
- Table/Metric Reasoner。
- Answer Composer。
- Verifier。
- Report Writer。

验收：

- 对事实查找、表格查询、指标计算、跨页归因四类问题均能生成答案。
- 答案包含 claim-level citations。
- 证据不足时能拒答或触发二次检索。
- Trace 可展示每个 Agent 节点。

### Phase 6：前端工作台

产出：

- 文档列表。
- PDF viewer。
- 问答面板。
- 引用高亮。
- Agent trace panel。
- Tool calls panel。
- Evidence graph panel。
- Table viewer。

验收：

- 点击答案引用跳转到具体页和 bbox。
- 用户能看到 Agent 工具调用顺序。
- 用户能展开某个 claim 的 evidence path。
- 页面布局适合录制 Demo。

### Phase 7：评测闭环

产出：

- 3 份公开 PDF。
- 60 条 long-PDF QA 数据。
- 5 种策略 runner。
- 指标计算。
- Evaluation panel。
- Benchmark report。

验收：

- 能对比 `text_only_vector`、`text_hybrid`、`layout_aware_hybrid`、`table_aware_agentic`、`evidence_graph_agent`。
- 输出 answer accuracy、citation precision、table QA accuracy、hallucination rate。
- 形成可放入 README 和简历的量化结果。

### Phase 8：项目包装

产出：

- README。
- 架构图。
- Demo runbook。
- 截图。
- 简历 bullets。
- 面试讲稿。
- 风险和未来扩展说明。

验收：

- 新用户按 README 能跑起来。
- 5 分钟内能完成核心 Demo。
- 项目描述能清楚区别于 RepoLens 和普通 PDF RAG。

## 4. 推荐 Demo 数据

P0 选择公开 PDF，避免版权和隐私问题。

候选类型：

- 上市公司 10-K / 年报。
- 公开招股书。
- 公开行业研究报告。
- arXiv 长论文。
- 技术标准白皮书。

推荐优先级：

1. 年报/10-K：表格多、跨页解释多、业务问题好设计。
2. 论文：图表多、实验表格多、适合科研问答。
3. 产品手册：版面复杂、适合定位步骤和限制。

## 5. P0 问题集设计

问题类型比例：

| 类型 | 数量 | 示例 |
| --- | --- | --- |
| 事实定位 | 10 | 某指标在哪一页出现，定义是什么 |
| 表格查找 | 12 | 2024 年某业务收入是多少 |
| 指标计算 | 10 | 毛利率同比变化多少 |
| 跨页归因 | 12 | 某指标下降的原因是什么 |
| 图表解释 | 8 | 图表展示的趋势是否和正文一致 |
| 风险总结 | 8 | 哪些风险可能影响利润率 |

每条问题必须有 gold evidence。

## 6. 技术难点拆解

### 6.1 PDF bbox 一致性

问题：

- PDF point 坐标、图片像素坐标、前端 canvas 坐标容易不一致。

策略：

- 后端统一保存 PDF 原始坐标。
- 页面 API 返回 scale 信息。
- 前端高亮时统一转换。
- 每个页面提供 debug overlay。

### 6.2 表格检索与计算

问题：

- 表格语义召回需要摘要，计算又需要结构化单元格。

策略：

- 表格保存两种形态：markdown summary + structured cells。
- 检索用 summary embedding 和表头 BM25。
- 计算只使用 structured cells。
- 计算结果保存 `derived_from` 边。

### 6.3 图表 Grounding

问题：

- P0 中直接做完整 chart understanding 成本高。

策略：

- P0 先做 figure bbox、caption 和附近正文 grounding。
- 图表问题回答时必须引用 figure/caption。
- P1 再接入 vision model 抽取图表趋势。

### 6.4 Agent 成本控制

问题：

- 多轮工具调用容易变慢、变贵。

策略：

- 每个问题设置工具调用上限。
- 先检索后扩展，只对 top evidence 扩展图邻域。
- 对表格和页面结果做摘要缓存。
- Verifier 只检查核心 claim。

## 7. 最小可行技术路线

如果时间有限，按这个最小闭环实现：

1. PyMuPDF 渲染 PDF 页面。
2. pdfplumber 提取文本和表格。
3. SQLite 存元数据。
4. 本地 BM25 + 可选 embedding adapter。
5. NetworkX 存 evidence graph。
6. FastAPI 提供工具 API。
7. LangGraph-style orchestrator 串联 Agent 节点。
8. Next.js 显示 PDF 页面、bbox 高亮和 trace。
9. JSONL 评测集跑策略对比。

## 8. 简历验收线

项目完成时，至少要能写出这类 bullet：

- 解析 3 份 100+ 页公开 PDF，构建包含 text/table/figure/page/section 的多模态 evidence graph，并支持 bbox 级证据跳转。
- 实现工具调用式 Agentic RAG，将问题分类、检索路由、表格读取、图邻域扩展、指标计算和 claim-level verifier 串成可追踪工作流。
- 自建 60 条长文档 QA 评测集，对比 5 种 RAG 策略，量化 citation precision、table QA accuracy、hallucination rate 和 latency。
- 在前端工作台展示 PDF 高亮、Agent trace、tool calls、evidence path 和 benchmark report，支持 5 分钟端到端 Demo。

