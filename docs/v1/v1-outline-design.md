# MAGE-Doc V1 概要设计：Evidence Graph Agentic RAG

## 1. V1 定位

V1 的目标是把 V0 的可演示长文档 RAG 闭环，升级成真正适合写进简历和面试深讲的 **Evidence Graph Agentic RAG 系统**。

V0 已经证明系统可以完成上传、页面渲染、文本/表格解析、检索、问答、引用和 bbox 高亮。V1 不再追求“多堆几个功能”，而是围绕一个核心问题加深：

> 当问题需要跨页、跨表格、跨章节、跨证据类型推理时，Agent 如何可追踪地收集、扩展、验证和引用证据？

因此 V1 的主线是：

```text
Evidence Graph -> Hybrid Retrieval -> Graph Expansion -> Agent Tools -> Claim Verification -> Evaluation
```

## 2. 与 V0 的关键区别

| 维度 | V0 | V1 |
| --- | --- | --- |
| 项目目标 | 跑通端到端 demo | 建立可讲深度的 Agentic RAG 架构 |
| 证据组织 | text/table evidence nodes | page-section-block-table-cell evidence graph |
| 检索方式 | 本地 BM25 风格检索 | lexical + semantic + graph expansion + rerank |
| Agent | 固定 deterministic workflow | 工具注册、计划执行、trace 持久化、二次证据扩展 |
| 引用 | 答案级 citations | claim-level evidence pack |
| 验证 | 基础 citation verification | claim support / partial / unsupported |
| 评测 | smoke check | 小型 benchmark、策略对比、指标报告 |
| 前端 | 文档页、问答、引用高亮 | 证据路径、工具轨迹、图邻域、验证结果 |

## 3. V1 目标

### 3.1 必须完成

- 建立 evidence graph 数据模型，显式保存节点、边、来源、bbox 和 parser metadata。
- 将 V0 的页面、文本块、表格节点接入图模型，支持 section、reading order、table cell、caption 候选关系。
- 实现 hybrid retrieval 基础能力，支持 keyword candidate、semantic candidate、graph expansion 和 rerank 分层组合。
- 实现 Agent tool registry，让工具输入输出、调用顺序、耗时和结果摘要可持久化审计。
- 实现 evidence pack，把一个答案拆成可验证 claim，并为每个 claim 绑定证据集合。
- 实现 claim-level verifier，至少支持 supported、partial、unsupported 和 insufficient evidence。
- 前端展示 evidence graph 邻域、agent trace、claim verification 和 citation path。
- 构建小型评测集，对比 V0 baseline 和 V1 evidence graph agent。

### 3.2 非目标

- 不在 V1 训练或微调版面分析模型。
- 不把 OCR 扫描版 PDF 做成主路径，OCR 留到 V2。
- 不实现完整大规模多文档知识库。
- 不强依赖外部付费 LLM 服务；外部模型只能作为可插拔 adapter。
- 不追求工业级权限、租户、队列和任务调度。

## 4. 总体架构

```text
PDF Upload
   |
   v
V0 Parsers
   |-- pages
   |-- text_blocks
   |-- tables
   v
Evidence Graph Builder
   |-- nodes: document/page/section/text_block/table/table_cell/caption
   |-- edges: contains/next/near/caption_of/part_of/supports
   v
Hybrid Retrieval Layer
   |-- lexical candidate
   |-- semantic candidate
   |-- graph expansion
   |-- rerank
   v
Agent Runtime
   |-- planner
   |-- tool registry
   |-- executor
   |-- verifier
   |-- trace store
   v
Answer + Evidence Pack
   |-- claim citations
   |-- bbox highlights
   |-- verification labels
   |-- evidence path
   v
Workbench UI + Evaluation
```

## 5. Evidence Graph 设计

### 5.1 节点类型

| 节点类型 | 作用 | V1 来源 |
| --- | --- | --- |
| `document` | 文档根节点 | 上传元数据 |
| `page` | PDF 页面节点 | V0 page rendering |
| `section` | 章节或标题范围 | 文本块标题候选和 reading order |
| `text_block` | 文本证据块 | V0 text parser |
| `table` | 表格证据块 | V0 table parser |
| `table_cell` | 单元格级证据 | 表格 matrix 和 cell bbox |
| `caption` | 表格/图附近说明文本 | layout heuristic |
| `answer_claim` | 答案中的可验证 claim | Agent answer composer |

V1 不要求一开始就完美识别 section 和 caption，但必须把模型设计成可逐步增强。

### 5.2 边类型

| 边类型 | 含义 | 用途 |
| --- | --- | --- |
| `contains` | document/page/section 包含下级节点 | 层级导航 |
| `next` | 阅读顺序中的下一个节点 | 跨块上下文扩展 |
| `near` | 版面上相邻或同页邻近 | 图邻域扩展 |
| `part_of` | cell 属于 table，caption 属于 section | 表格结构和引用 |
| `caption_of` | caption 解释 table 或 figure | 多模态 grounding |
| `mentions` | 节点提到实体、指标或年份 | 查询扩展 |
| `supports` | evidence 支持某个 answer_claim | verifier 输出 |
| `contradicts` | evidence 与 claim 冲突 | verifier 输出 |

### 5.3 图存储策略

V1 继续使用 SQLite，优先保证本地可运行和可审计：

- `evidence_nodes` 作为统一节点表继续扩展。
- 新增 `evidence_edges` 表保存有向边、权重、来源和 metadata。
- 新增 graph service 封装邻域查询、路径查询和 evidence pack 构建。
- 暂不引入独立图数据库，避免部署复杂度掩盖项目主线。

## 6. Hybrid Retrieval 设计

V1 检索分四层：

1. **Lexical candidate**：保留 V0 的本地 BM25 风格检索，适合精确术语、指标名、年份、表头。
2. **Semantic candidate**：新增 embedding adapter，支持本地轻量实现和可选外部模型实现。
3. **Graph expansion**：对 top evidence 扩展 section、page、table、caption、nearby blocks 和 next blocks。
4. **Rerank**：将 query relevance、node type、graph distance、page proximity、table/caption boost 合并为最终排序。

核心原则：

- 召回尽量宽，答案证据必须窄。
- graph expansion 只对 top candidate 执行，避免无边界扩散。
- 每一步都要输出 trace item，方便前端和评测解释。

## 7. Agent Runtime 设计

### 7.1 角色划分

| 组件 | 职责 |
| --- | --- |
| Question Analyzer | 判断问题是否偏文本、表格、跨页、计算、归因或图表说明 |
| Planner | 生成工具调用计划 |
| Tool Registry | 管理工具 schema、输入输出和审计配置 |
| Executor | 按计划调用工具，收集中间结果 |
| Evidence Collector | 把搜索结果、图邻域和表格读取结果组装成 evidence pack |
| Answer Composer | 生成带 claim 和 citation 的答案结构 |
| Verifier | 对每个 claim 做证据支持判断 |
| Trace Store | 持久化每一步工具调用和关键决策 |

### 7.2 V1 工具集合

| 工具 | 输入 | 输出 |
| --- | --- | --- |
| `search_evidence` | query, scope, node_types | candidate evidence nodes |
| `expand_graph` | node_ids, edge_types, depth | graph neighborhood |
| `inspect_page` | page_id | page image metadata and page nodes |
| `read_table` | table_node_id | structured rows, cells, headers |
| `compare_evidence` | claim, evidence_ids | support signals |
| `verify_claims` | answer claims, evidence pack | verification labels |
| `explain_trace` | question_id | planner/tool/verifier timeline |

V1 先保持 deterministic agent，保证可测、可复现。后续可以把 Planner 替换成 LLM planner，但工具 schema 和 trace store 不变。

## 8. Evidence Pack 与 Claim Verification

V1 的答案结构不再只是自然语言加 citations，而是：

```json
{
  "answer": "...",
  "claims": [
    {
      "claim": "...",
      "status": "supported",
      "citations": ["evidence_node_id"],
      "verification_reason": "..."
    }
  ],
  "evidence_pack": {
    "nodes": [],
    "edges": [],
    "trace": []
  }
}
```

Verifier 的第一版采用可解释规则和检索信号：

- claim 中的数字、年份、实体必须能在引用证据中找到。
- 表格 claim 必须引用 table 或 table_cell。
- 跨页归因 claim 至少需要多个 evidence nodes。
- 引用缺失、类型不匹配或关键数字不匹配时标记为 `partial` 或 `unsupported`。

## 9. 前端工作台设计

V1 前端继续沿用 V0 workbench，但增加三个强展示面板：

| 面板 | 价值 |
| --- | --- |
| Evidence Graph Panel | 展示当前答案使用的节点、边、邻域和路径 |
| Agent Trace Panel | 展示 planner、tool calls、retrieval、graph expansion、verifier |
| Claim Verification Panel | 展示每个 claim 的 supported / partial / unsupported 状态 |

核心交互：

- 点击 claim，PDF viewer 高亮该 claim 的引用证据。
- 点击 graph node，跳转到对应 page 和 bbox。
- 点击 trace step，展示该工具的输入输出摘要。
- 表格证据可展开为 row/cell 视图。

## 10. Evaluation 设计

V1 必须形成量化结果，而不是只靠 demo 观感。

### 10.1 数据集

- 先选择 2 到 3 份公开 PDF。
- 每份文档至少 10 到 20 条问题。
- 每条问题记录 gold answer、gold evidence page、gold evidence node type 和问题类型。

### 10.2 策略对比

至少对比：

| 策略 | 说明 |
| --- | --- |
| `v0_bm25_baseline` | V0 检索和固定 agent |
| `hybrid_no_graph` | lexical + semantic，但不扩图 |
| `graph_expansion_only` | top lexical + graph expansion |
| `evidence_graph_agent` | V1 完整流程 |

### 10.3 指标

- answer contains gold key facts。
- citation page hit。
- citation node type match。
- table QA accuracy。
- unsupported claim rate。
- average tool calls。
- latency。

## 11. 技术选型

| 模块 | 选择 | 原因 |
| --- | --- | --- |
| 后端 | FastAPI | 延续 V0，接口清晰 |
| 存储 | SQLite | 本地可运行、可审计、适合简历项目 |
| PDF 解析 | PyMuPDF | 已验证页面渲染、文本和表格路径 |
| Graph | SQLite edge table + service layer | 比 NetworkX 更容易持久化和 API 化 |
| 检索 | 本地 lexical + pluggable embedding adapter | 兼顾可运行与可扩展 |
| Agent | Deterministic tool workflow first | 可测试、可复现，后续可换 LLM planner |
| 前端 | Next.js | 延续 V0 workbench |
| 评测 | JSONL fixtures + pytest/CLI runner | 易维护、可自动化 |

## 12. 风险与取舍

| 风险 | 影响 | 策略 |
| --- | --- | --- |
| section/caption 识别不稳定 | 图边质量下降 | 先用 heuristic，并保留 parser metadata |
| semantic retrieval 引入外部依赖 | 本地复现变难 | adapter 设计，默认本地 fallback |
| graph expansion 噪声过多 | evidence pack 变乱 | 限制 depth、edge type 和 top-k |
| verifier 过度复杂 | 阶段失控 | V1 先做规则和信号验证 |
| 前端图可视化耗时 | 影响交付 | 先实现 evidence path 列表，再增强图视图 |

## 13. 简历表达目标

V1 完成后，项目应该能支撑这类简历 bullet：

- 设计并实现长 PDF 多模态 evidence graph，将 page、section、text block、table、table cell 和 caption 统一为可查询证据节点，并支持 bbox 级引用跳转。
- 实现 hybrid retrieval + graph expansion 的 Agentic RAG 流程，使 Agent 可根据问题类型调用检索、读表、扩图、验证等工具，并持久化完整 tool trace。
- 构建 claim-level verifier，将答案拆解为可验证 claim，并用 evidence pack 标记 supported、partial 和 unsupported，降低长文档问答幻觉。
- 自建小型长文档 QA 评测集，对比 V0 baseline、hybrid retrieval 和 evidence graph agent，输出 citation hit、table QA、unsupported claim rate 和 latency 指标。
