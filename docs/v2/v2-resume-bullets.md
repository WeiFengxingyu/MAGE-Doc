# MAGE-Doc V2 Resume Bullets

## 中文简历版

- 设计并实现 MAGE-Doc：基于多模态证据图的长文档 Agentic RAG 系统，将 PDF 解析为 text/table/OCR/chart/metric evidence nodes，并通过 page、bbox、graph edge 支撑可追溯引用。
- 在 V1 Evidence Graph RAG 基础上扩展 V2 Advanced Multimodal Agent Platform，实现 OCR substrate、vision grounding、metric graph、多文档 collection、MCP-compatible tool server、benchmark adapter 与 failure diagnosis。
- 构建 Agent 工具链 `search_doc / inspect_page / read_table / build_evidence_pack / verify_claims`，支持内部问答 API 与外部 Agent 通过 MCP-style envelope 调用同一套能力。
- 搭建 benchmark-ready eval harness，新增 `v2_multimodal_graph` strategy，输出 JSON/Markdown report 与 failure distribution，将失败归因为 retrieval miss、graph miss、citation mismatch、unsupported claim 等可修复类型。

## English Resume Version

- Built MAGE-Doc, a multimodal Agentic RAG system for long-PDF reasoning that converts PDFs into text/table/OCR/chart/metric evidence nodes with page coordinates, bounding boxes, and evidence graph relations.
- Extended the V1 evidence graph RAG pipeline into a V2 advanced multimodal agent platform with OCR substrate, vision grounding, metric graph, multi-document collections, MCP-compatible tools, benchmark adapter, and failure diagnosis.
- Exposed core document intelligence tools through a unified tool layer, including `search_doc`, `inspect_page`, `read_table`, `build_evidence_pack`, and `verify_claims`, enabling both internal API workflows and external Agent-style calls.
- Implemented a benchmark-ready evaluation harness with a `v2_multimodal_graph` strategy, JSON/Markdown reports, and explainable failure diagnosis for retrieval miss, graph miss, citation mismatch, unsupported claim, OCR confidence, and visual grounding issues.

