# MAGE-Doc V2 概要设计：Advanced Multimodal Agent Platform

## 1. V2 定位

V2 的目标是把 V1 的 Evidence Graph Agentic RAG 强项目，升级成更前沿的 **Advanced Multimodal Agent Platform**。

V1 已经完成：

```text
Evidence Graph -> Hybrid Retrieval -> Evidence Pack -> Trace Store -> Claim Verification -> Evaluation -> Workbench Demo
```

V2 不再只是增强检索，而是把 MAGE-Doc 推向更接近真实复杂文档智能平台的方向：

```text
OCR + Vision Grounding + Multi-Document Collection + MCP Tools + Benchmark Adapter + Failure Diagnosis
```

核心问题：

> 当文档包含扫描页、图表、跨页表格、多文档证据和外部 Agent 调用时，系统如何仍然保持可观测、可验证、可评测？

## 2. 与 V1 的关键区别

| 维度 | V1 | V2 |
| --- | --- | --- |
| 文档类型 | born-digital PDF 为主 | 支持扫描页、图片页、混合 PDF |
| 图表理解 | caption/near text grounding | vision-assisted chart grounding |
| 数据范围 | 单文档 | 多文档 collection |
| Agent 入口 | 内置问答 API | MCP Server + 外部 Agent 可调用 |
| 表格能力 | 单页表格和 table_cell | 跨页表格合并与 metric graph |
| 评测 | synthetic local eval | benchmark adapter + failure diagnosis |
| 简历价值 | 主项目深度 | 前沿平台化增强 |

## 3. V2 必须完成

- OCR pipeline：扫描页检测、OCR 文本节点、bbox 对齐、OCR confidence。
- Vision grounding：figure/chart 区域、caption、视觉摘要、趋势声明和 bbox 绑定。
- Multi-document collection：collection、document membership、跨文档检索和引用。
- MCP Server：暴露 `search_doc`、`inspect_page`、`read_table`、`build_evidence_pack` 等工具。
- Evaluation adapter：为外部 benchmark/TREC RAG 风格数据准备输入输出适配器。
- Failure diagnosis：记录 retrieval miss、citation mismatch、claim unsupported 等失败类型。
- Workbench 增强：展示 OCR/vision/collection/MCP/eval diagnosis 的状态和报告入口。

## 4. V2 非目标

- 不训练 OCR 或视觉模型。
- 不承诺完全自动理解所有复杂图表。
- 不做生产级多租户、权限和计费。
- 不做大规模向量数据库部署。
- 不为了接入外部 benchmark 破坏本地 demo 可运行性。

## 5. 总体架构

```text
PDF / Image PDF / Scanned PDF
   |
   v
Document Intake
   |-- born-digital parser
   |-- scanned-page detector
   |-- OCR adapter
   v
Multimodal Evidence Graph
   |-- text_block
   |-- ocr_text_block
   |-- table / table_cell
   |-- figure / chart / caption
   |-- metric / entity / year
   v
Collection Retrieval
   |-- single-document evidence pack
   |-- cross-document evidence pack
   |-- graph expansion
   v
Agent Runtime
   |-- internal question API
   |-- MCP tools
   |-- failure diagnosis
   |-- benchmark adapter
   v
Workbench + Reports
```

## 6. V2 核心模块

### 6.1 OCR Pipeline

目标：

- 检测扫描页或低文本密度页面。
- 对页面图像执行 OCR。
- OCR 结果进入 `evidence_nodes`。
- bbox 与 PDF page 坐标保持一致。

默认策略：

- 先实现 adapter 接口和可测试 fallback。
- 如果本机有 OCR runtime，再接入真实 OCR。
- 没有 OCR runtime 时使用 mock OCR fixture 保证测试闭环。

### 6.2 Vision Grounding

目标：

- 建立 `figure`、`chart`、`visual_summary` 节点。
- 将 chart/figure 与 caption、near text 绑定。
- 支持图表问题引用 visual evidence。

默认策略：

- V2 先做 figure/chart region + caption/near text + optional vision summary。
- Vision model 作为 adapter，不强制依赖外部 API。

### 6.3 Metric Graph

目标：

- 从表格和文本中抽取 metric、year、entity、value。
- 保存 `metric_value` 节点或 metadata。
- 支持简单同比、差值、趋势解释。

### 6.4 Multi-Document Collection

目标：

- 用户可以创建 collection。
- 多个 document 加入 collection。
- collection-level search 和 ask。
- 引用必须包含 document_id、filename、page_number 和 bbox。

### 6.5 MCP Server

目标：

- 将 MAGE-Doc 工具暴露给外部 Agent。
- 最小工具：
  - `search_doc`
  - `inspect_page`
  - `read_table`
  - `build_evidence_pack`
  - `verify_claims`

### 6.6 Benchmark Adapter

目标：

- 将外部 QA case 转为内部 eval case。
- 将内部 answer/evidence pack 转为 benchmark submission 格式。
- 支持 TREC/RAG-style 文本输入输出，不承诺直接参赛。

### 6.7 Failure Diagnosis

目标：

- 对失败样例自动归因：
  - retrieval miss。
  - graph expansion miss。
  - citation mismatch。
  - unsupported claim。
  - OCR low confidence。
  - visual grounding missing。
- 输出 failure report，指导后续修复。

## 7. 数据模型方向

新增或扩展：

| 模型 | 说明 |
| --- | --- |
| `collections` | 多文档集合 |
| `collection_documents` | collection 与 document 关系 |
| `ocr_runs` | OCR 运行记录 |
| `vision_runs` | vision grounding 运行记录 |
| `benchmark_runs` | benchmark/eval 运行记录 |
| `failure_diagnoses` | 失败诊断记录 |

证据节点扩展：

- `ocr_text_block`
- `figure`
- `chart`
- `visual_summary`
- `metric_value`

边扩展：

- `derived_from`
- `visualizes`
- `same_metric`
- `same_entity`
- `cross_doc_supports`

## 8. 技术选型

| 模块 | 默认选型 | 原因 |
| --- | --- | --- |
| OCR | Adapter + optional Tesseract/PaddleOCR/EasyOCR | 避免强依赖，保留可扩展 |
| Vision | Adapter + local fixture first | 保证本地闭环 |
| Collection | SQLite tables | 延续本地可运行 |
| MCP | Python MCP-compatible server module | 平台化加分 |
| Eval | JSONL + Python runner | 延续 V1 harness |
| Diagnosis | Rule-based first | 可解释、可测试 |

## 9. V2 验收线

V2 完成时应满足：

- 扫描页能产生 OCR evidence nodes，并能被检索和引用。
- 图表问题能引用 figure/chart/caption/visual_summary 证据。
- collection-level 问答能跨多个文档返回带文档名的引用。
- 外部 Agent 能通过 MCP 调用至少 3 个 MAGE-Doc 工具。
- Eval adapter 能输出 benchmark-style report。
- Failure diagnosis 能为失败 case 给出原因分布。
- README、runbook、eval report 和简历 bullets 更新。

## 10. 简历表达目标

V2 完成后可支撑：

- 在 V1 evidence graph agent 基础上，扩展 OCR、vision grounding 和 multi-document collection，使系统支持扫描 PDF、图表证据和跨文档问答。
- 设计 MCP tool server，将文档检索、页面检查、表格读取、evidence pack 和 claim verification 暴露给外部 Agent。
- 构建 benchmark adapter 与 failure diagnosis，将 RAG 失败归因为 retrieval miss、citation mismatch、unsupported claim、OCR low confidence 等可修复类型。
