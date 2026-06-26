# MAGE-Doc 版本路线图

## 1. 总体策略

MAGE-Doc 不建议一步到位实现完整多模态长文档 Agent。最优路线是分 3 个大版本推进：

- **V0：MVP 可演示闭环**  
  先完成 PDF 上传、页面渲染、文本/表格解析、证据定位、基础 Agentic RAG 和引用高亮。

- **V1：简历级强项目版本**  
  加入 evidence graph、表格计算、图表 grounding、claim-level verifier、Agent trace 和评测闭环。

- **V2：前沿增强版本**  
  加入视觉模型、扫描版 OCR、跨页表格合并、多文档 collection、MCP Server 和 TREC/RAG 适配器。

这样做的好处：

1. V0 很快能跑通端到端 Demo。
2. V1 能支撑简历和面试深讲。
3. V2 保留前沿扩展，不拖慢早期交付。

## 2. 版本目标

| 版本 | 名称 | 目标 | 简历价值 |
| --- | --- | --- | --- |
| V0 | Long-PDF RAG MVP | 上传 PDF、解析文本/表格、问答、引用页码和 bbox | 证明项目可运行 |
| V1 | Multimodal Evidence Graph Agent | 多模态证据图、工具调用 Agent、表格计算、Verifier、评测 | 主简历版本 |
| V2 | Advanced Multimodal Agent Platform | 图表视觉理解、OCR、多文档、MCP、外部 benchmark | 前沿增强 |

## 3. V0：MVP 可演示闭环

### 3.1 范围

V0 只追求“能上传、能解析、能问答、能引用、能展示 trace”。

必须包含：

- FastAPI + Next.js 项目骨架。
- PDF 上传和文档列表。
- PDF 页面渲染。
- 文本块解析和 bbox 保存。
- 基础表格解析。
- BM25 或简单 hybrid retrieval。
- 基础 Agentic RAG 流程。
- 答案引用和 PDF 区域高亮。
- Tool call / Agent trace 基础展示。

不包含：

- 完整图表视觉理解。
- 扫描版 OCR。
- 跨页表格合并。
- 多文档问答。
- 复杂 benchmark。

### 3.2 验收标准

- 上传一份 50+ 页 PDF 后可以浏览页面。
- 对文本问题能返回带页码和 bbox 的答案。
- 对表格问题能定位到表格并读取单元格文本。
- 点击引用可以跳转到 PDF 页面并高亮证据。
- Trace 面板能展示检索、读页、生成、验证等步骤。

## 4. V1：简历级强项目版本

### 4.1 范围

V1 是真正写进简历的主版本。

必须包含：

- `page-section-block-table-figure-cell` evidence graph。
- text/table/page/figure/graph 工具注册和调用审计。
- 问题分类和工具路由。
- 多轮证据收集。
- Evidence graph 邻域扩展。
- 表格结构化读取和指标计算。
- Claim-level verifier。
- Evidence pack。
- 可视化 evidence path。
- 至少 3 份公开 PDF 和 60 条 QA 评测集。
- 5 种策略对比评测。

### 4.2 验收标准

- 能回答跨页归因问题。
- 能回答表格查找和简单计算问题。
- 能引用 figure/caption 或附近正文回答图表相关问题。
- 每个关键 claim 都有 supported / partial / unsupported 判断。
- 评测报告能给出 answer accuracy、citation precision、table QA accuracy、hallucination rate。
- README、截图、demo runbook、简历 bullets 完整。

## 5. V2：前沿增强版本

### 5.1 范围

V2 用于进一步拔高项目，但不阻塞 V1 收尾。

可选增强：

- OCR 支持扫描版 PDF。
- Vision model 解析图表趋势、legend 和坐标轴。
- 表格跨页合并。
- Metric graph：指标、年份、实体、计算关系。
- 多文档 collection 问答。
- MCP Server，把 MAGE-Doc 工具暴露给外部 Agent。
- TREC RAG 文本适配器。
- RAG failure diagnosis 和局部修复。
- Agent 成本优化和缓存。

### 5.2 验收标准

- 图表问题不只依赖 caption，还能引用视觉描述。
- 扫描版 PDF 能 OCR 并进入同一 evidence graph。
- 外部 Agent 能通过 MCP 调用 `search_doc`、`inspect_page`、`read_table` 等工具。
- 对外部 benchmark 或自建 benchmark 有稳定报告。

## 6. 推荐实际执行路线

推荐路线：

```text
Batch 1: V0 Foundation
Batch 2: V1 Evidence Graph Agentic RAG
Batch 3: V2 Advanced Multimodal Agent Platform
Batch 4: V2 OCR and Vision Grounding
Batch 5: V2 Collection, MCP, Benchmark, and Diagnosis
```

当前 V0 和 V1 已完成，下一步应该开始的是：

> **Batch 3：V2 Advanced Multimodal Agent Platform**

原因：

- V0 已经打通上传、渲染、解析、检索、问答、引用和高亮。
- V1 已经完成 evidence graph、hybrid retrieval、evidence pack、trace store、claim verification、evaluation 和 workbench polish。
- V2 可以在 V1 底座上继续扩展 OCR、vision grounding、multi-document collection、MCP server、benchmark adapter 和 failure diagnosis。

## 7. 当前执行入口

V2 的执行入口已经拆分为独立文档：

- `docs/v2/v2-outline-design.md`：V2 概要设计。
- `docs/v2/v2-implementation-plan.md`：V2 分阶段实现计划。
- `docs/v2/batch3-worklog.md`：V2 大阶段工作日志。

推荐下一步：

```text
V2 Phase 1: OCR Substrate
```

Phase 1 必须先写详细设计文档，再实现 scanned-page detector、OCR adapter、OCR run model、`ocr_text_block` evidence nodes 和检索闭环。
