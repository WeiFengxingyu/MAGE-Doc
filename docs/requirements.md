# MAGE-Doc 需求文档

## 1. 项目定位

MAGE-Doc 是一个面向长 PDF、表格、图表和复杂版面的多模态 Agentic RAG 系统。它不定位为普通“上传 PDF 问答助手”，而定位为一个可解释、可评测、可演示的长文档证据推理平台。

核心目标：

- 将长 PDF 解析为文本、标题、段落、表格、图片、图表、脚注、页眉页脚等结构化元素。
- 构建 `Document -> Page -> Section -> Block -> Table/Figure/Cell` 的多模态证据图。
- 让 Agent 根据问题动态选择检索、读页、读表、看图、扩展邻域、验证证据等工具。
- 输出带页码、区域、表格单元格、图表来源和证据路径的 grounded answer。
- 提供 Agent trace、证据高亮、失败诊断和评测指标，证明系统不是黑盒问答。

推荐简历标题：

> MAGE-Doc：基于多模态证据图的长文档 Agentic RAG 系统

推荐英文副标题：

> Multimodal Agentic RAG for Long-PDF Reasoning with Evidence Graphs

## 2. 与已有 RepoLens 的差异

| 维度 | RepoLens | MAGE-Doc |
| --- | --- | --- |
| 场景 | 代码仓库理解、代码 QA、PR/MR Review | 长 PDF 理解、表格/图表问答、跨页证据推理 |
| 数据对象 | 代码文件、symbol、diff、代码图谱 | PDF 页面、版面块、表格、图表、章节、脚注 |
| 图结构 | 文件、类、函数、调用、import | 页面、章节、段落、表格、图片、单元格、引用关系 |
| RAG 重点 | 代码 GraphRAG、symbol-aware retrieval | Multimodal RAG、layout-aware retrieval、evidence graph |
| Agent 工具 | code_search、read_file_slice、diff analysis | inspect_page、read_table、describe_figure、trace_evidence_graph |
| Demo 价值 | 开发者工具、代码智能体 | 金融/科研/医疗/企业文档智能体 |
| 简历关键词 | Code Agent、GraphRAG、MCP、PR Review | Multimodal Agentic RAG、Long Document Reasoning、Table/Chart Grounding |

因此，MAGE-Doc 可以作为第二个核心项目，和 RepoLens 形成互补：

- RepoLens 展示“代码智能体和代码结构化理解”。
- MAGE-Doc 展示“多模态长文档智能体和证据推理”。

## 3. 目标用户与场景

### 3.1 目标用户

- 金融分析师：阅读年报、招股书、研报，追踪财务指标、业务风险和管理层解释。
- 科研人员：阅读长论文、技术报告和实验表格，定位实验设置、指标和图表结论。
- 法务/合规人员：阅读政策、合同、审计报告，查找条款冲突和证据来源。
- 产品/工程人员：阅读复杂产品手册、标准文档、技术白皮书，定位参数、流程和限制。

### 3.2 P0 推荐演示场景

P0 优先选择“上市公司年报/招股书/研报”作为 demo 语料，因为这类文档同时包含：

- 长篇文本和章节层级。
- 大量财务表格。
- 图表和指标说明。
- 跨章节因果解释。
- 适合问复杂、可验证、带证据的问题。

示例问题：

- “2024 年毛利率下降的主要原因是什么？请结合财务表格和管理层讨论回答。”
- “研发费用增长是否伴随收入增长？请引用对应表格和文字说明。”
- “现金流变差的原因是什么？是否和应收账款或存货变化有关？”
- “报告中哪些风险因素可能影响未来利润率？请按风险等级归纳。”
- “图表中的区域收入变化和管理层叙述是否一致？”

## 4. 核心问题

普通 PDF RAG 往往失败在以下问题：

1. **版面丢失**：PDF 转文本后丢失标题层级、表格结构、图表位置和跨栏阅读顺序。
2. **表格不可推理**：表格被切成碎片，无法精确引用单元格，也无法做指标计算。
3. **图表不可追踪**：图像或图表只被当成图片，无法与正文解释建立关联。
4. **长文档证据分散**：答案往往需要跨页、跨章节、跨表格组合证据。
5. **Top-k 不可靠**：一次性向量检索容易召回语义相近但证据不足的片段。
6. **引用粗糙**：只引用 chunk 或页码，无法定位到具体区域、表格行列或图表。
7. **缺少验证**：模型生成的解释可能和表格数字不一致。

MAGE-Doc 的核心挑战是：

> 如何让 Agent 在长 PDF 中像人一样先浏览结构，再按问题动态打开页面、读取表格、检查图表、追踪相邻证据，并生成可验证答案。

## 5. 功能需求

### 5.1 文档导入与解析

系统应支持上传或导入 PDF 文件，并生成文档解析任务。

P0 范围：

- 支持单个 PDF 导入。
- 记录文档元数据：文件名、页数、大小、解析状态、解析耗时。
- 渲染每页缩略图或页面图片，用于前端证据高亮。
- 提取页面文本块、坐标、字体大小、粗细、阅读顺序。
- 识别标题、段落、列表、页眉页脚、脚注候选。
- 提取表格结构，包括表格所在页、bbox、行列、单元格文本。
- 提取图片/图表区域，包括 bbox、caption 候选、附近说明文本。

P1 扩展：

- OCR 支持扫描版 PDF。
- 图表 caption 与正文引用关系识别。
- 表格跨页合并。
- 公式、脚注、附录识别。
- 多 PDF collection 管理。

### 5.2 多模态证据图

系统应将解析结果构建为 evidence graph。

节点类型：

- `document`
- `page`
- `section`
- `text_block`
- `table`
- `table_row`
- `table_cell`
- `figure`
- `caption`
- `footnote`
- `metric`
- `claim`

边类型：

- `contains`：文档包含页面，页面包含块。
- `belongs_to_section`：块属于章节。
- `next_block`：阅读顺序相邻。
- `nearby`：版面相邻。
- `caption_of`：caption 描述图表或表格。
- `mentions`：文本提到指标、年份、实体、表格编号、图编号。
- `supports`：证据支持某个 claim。
- `contradicts`：证据与某个 claim 冲突。
- `derived_from`：计算指标来自某些单元格。

每个证据节点必须保存：

- 文档 ID。
- 页码。
- bbox。
- 文本或结构化内容。
- 来源类型。
- 置信度。
- 解析器来源。

### 5.3 检索与工具调用

系统应提供 Agent 可调用的结构化工具。

P0 工具：

| 工具 | 作用 |
| --- | --- |
| `search_text` | 基于关键词、向量和元数据检索文本块 |
| `search_tables` | 按指标、年份、实体、表头检索表格 |
| `inspect_page` | 打开指定页，返回页面 blocks、tables、figures 和缩略图坐标 |
| `read_table` | 读取表格结构、行列、单元格和 caption |
| `inspect_figure` | 读取图表区域、caption、附近正文和可选视觉描述 |
| `expand_evidence_graph` | 从一个证据节点扩展章节、相邻块、caption、表格单元格 |
| `calculate_metric` | 对表格单元格执行增长率、占比、差值等安全计算 |
| `verify_answer` | 检查答案中的 claim 是否有证据支撑 |

P1 工具：

- `compare_tables`
- `trace_metric`
- `detect_conflict`
- `summarize_section`
- `export_evidence_pack`
- `run_trec_adapter`

### 5.4 Agentic RAG 工作流

系统应采用可追踪的多阶段 Agentic RAG，而不是一次性检索。

推荐节点：

1. **Question Classifier**
   - 判断问题类型：事实查找、表格计算、图表解释、跨页归因、风险总结、对比分析。

2. **Plan Agent**
   - 将问题拆成子任务。
   - 决定需要哪些证据类型。
   - 生成工具调用计划。

3. **Router Agent**
   - 根据子任务选择 text/table/figure/page/graph 工具。

4. **Evidence Collector**
   - 多轮检索证据。
   - 保存每次工具调用、输入、输出、耗时、token 和候选证据。

5. **Evidence Graph Expander**
   - 对高相关证据扩展同页、同章节、caption、表格、附近说明。

6. **Table/Metric Reasoner**
   - 对表格型问题做结构化读取和可验证计算。

7. **Answer Composer**
   - 生成带引用的答案。
   - 每个关键 claim 绑定证据节点。

8. **Verifier**
   - 检查 claim 是否有证据支撑。
   - 检查表格数字是否一致。
   - 检查是否引用错误页或错误单元格。
   - 对证据不足的问题触发二次检索或拒答。

9. **Report Writer**
   - 输出最终答案、证据列表、推理路径和置信度。

### 5.5 前端工作台

P0 应实现一个可演示的工作台，而不是只提供 API。

核心视图：

- 文档列表和解析状态。
- PDF 页面浏览器。
- 问答面板。
- Agent trace 面板。
- Evidence graph 面板。
- Evidence pack 面板。
- 表格查看器。
- 引用高亮：点击答案引用后跳转到对应页和 bbox。
- 评测面板：展示准确率、引用覆盖率、幻觉率、延迟、工具调用次数。

交互要求：

- 用户可以上传 PDF 并查看解析进度。
- 用户可以提问并实时查看工具调用轨迹。
- 用户点击引用后，页面定位到证据区域。
- 用户可以展开证据路径：answer claim -> evidence node -> page/table/figure。
- 用户可以查看 verifier 对每条 claim 的判断。

### 5.6 评测需求

系统必须包含评测闭环，这是简历加分关键。

P0 数据集：

- 至少 3 份长 PDF。
- 至少 60 条问题。
- 每条问题标注：
  - 问题类型。
  - 标准答案要点。
  - 支持证据页码。
  - 支持证据 bbox 或表格单元格。
  - 是否需要计算。
  - 是否需要跨页。

指标：

| 指标 | 说明 |
| --- | --- |
| `answer_accuracy` | 答案要点命中率 |
| `citation_coverage` | 关键 claim 是否有引用 |
| `citation_precision` | 引用是否指向正确证据 |
| `table_qa_accuracy` | 表格问答或计算正确率 |
| `figure_grounding_rate` | 图表相关问题是否引用正确图表 |
| `evidence_recall_at_k` | 检索候选中是否包含标注证据 |
| `faithfulness_score` | 回答是否被证据支持 |
| `hallucination_rate` | 无证据 claim 占比 |
| `tool_call_count` | 平均工具调用次数 |
| `latency_p95` | P95 延迟 |
| `token_cost` | 平均 token 成本 |

对比策略：

- `text_only_vector`
- `text_hybrid`
- `layout_aware_hybrid`
- `table_aware_agentic`
- `multimodal_evidence_graph_agent`

简历中应最终沉淀 2 到 4 个真实数字，例如：

- 相比 text-only RAG，citation precision 提升 X%。
- 表格问答准确率达到 X%。
- 幻觉率下降 X%。
- 多模态证据图策略在跨页问题上 recall@5 提升 X%。

## 6. 非功能需求

### 6.1 可解释性

- 所有回答必须展示引用。
- 所有引用必须能跳转到 PDF 页面的具体区域。
- 每个 Agent 步骤必须有 trace。
- 每个工具调用必须记录输入、输出摘要、耗时和错误。

### 6.2 安全性

- 上传文件大小限制。
- 文档解析任务隔离。
- 禁止执行 PDF 内嵌脚本。
- 工具调用只读优先。
- 对 LLM 输出进行证据约束，缺少证据时必须显式说明。

### 6.3 可扩展性

- 解析层、索引层、Agent 层、评测层解耦。
- 支持替换 OCR、layout parser、embedding model、reranker、vision model。
- 支持单文档和多文档 collection 扩展。

### 6.4 可复现性

- 提供 demo PDFs 或公开可下载数据说明。
- 提供固定评测集。
- 提供 Docker Compose 本地部署。
- 所有评测运行保留配置快照。

## 7. P0 / P1 / P2 范围

### P0：面试可演示闭环

- PDF 上传和页面渲染。
- 文本块、表格、图片区域基础解析。
- 多模态 evidence graph 存储。
- text/table/page/graph 工具。
- Agentic RAG 问答链路。
- 答案引用和页面 bbox 高亮。
- Agent trace。
- 60 条评测样例和基础指标。
- README、架构图、demo runbook。

### P1：深度增强

- OCR 和扫描版 PDF。
- 图表视觉理解。
- 表格跨页合并。
- 指标实体抽取和 metric graph。
- Claim-level verifier。
- 失败诊断和局部重试。
- TREC RAG 文本评测适配器。

### P2：生产化探索

- 多用户和权限。
- 多文档 collection。
- 异步任务队列。
- 缓存和增量索引。
- MCP Server，让外部 Agent 调用 MAGE-Doc 工具。
- 领域模板：财报分析、科研论文、合规审计、产品手册。

## 8. 简历表达

推荐项目描述：

> MAGE-Doc：基于多模态证据图的长文档 Agentic RAG 系统。系统解析长 PDF 中的文本、表格、图表和版面结构，构建页面级 evidence graph，并通过工具调用式 Agent 实现动态检索、跨页推理、表格计算、证据高亮和忠实性评测。

推荐 bullet：

- 设计 PDF layout-aware 解析链路，提取 text/table/figure/page/section 多模态节点，构建支持跨页扩展和证据追踪的 evidence graph。
- 实现 Agentic RAG 工作流，支持问题分类、工具路由、多轮证据收集、表格计算、图表证据检查、claim-level verifier 和证据不足拒答。
- 构建可视化工作台，展示 PDF 区域高亮、Agent trace、tool calls、evidence path 和评测指标，提升长文档问答的可解释性。
- 自建长文档评测集，对比 text-only、hybrid、layout-aware、table-aware 和 evidence-graph agent 策略，量化 answer accuracy、citation precision、hallucination rate 和 table QA accuracy。

## 9. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 多模态范围过大 | 项目难以完成 | P0 先做文本、表格、图片区域和 caption，图表视觉理解放 P1 |
| PDF 解析质量不稳定 | 证据定位错误 | 保留 bbox、parser confidence 和人工可视化校正入口 |
| 表格跨页复杂 | 表格 QA 准确率低 | P0 只支持单页表格，P1 再做跨页合并 |
| Agent 成本高 | 延迟和费用不可控 | 加入预算控制、工具调用上限、证据裁剪和缓存 |
| 评测标注耗时 | 无法量化效果 | 先用 3 份公开 PDF + 60 条高质量问题构建小而硬的数据集 |

