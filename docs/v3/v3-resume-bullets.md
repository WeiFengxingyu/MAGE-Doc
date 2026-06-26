# MAGE-Doc V3 Resume Bullets

## 中文简历版

- 在多模态 Evidence Graph Agentic RAG 基础上实现 V3 Failure-Aware Self-Correcting Agent，构建 diagnosis -> repair policy -> repair trace -> reliability evaluation 的可靠性闭环。
- 设计 Evidence Sufficiency Scoring，将 answer term hit、citation type hit、claim support、graph context、OCR/visual signals 聚合为可解释评分，并用关键门控避免证据不足时误判为 supported。
- 实现 Repair Policy Engine，将 retrieval miss、graph miss、citation mismatch、unsupported claim 等失败类型映射为 query rewrite、node type expansion、graph depth expansion、citation rerank、conservative answer rewrite 等可执行动作。
- 构建 V3 curated benchmark suite 和 reliability report，对比 baseline 与 self-correcting strategy，输出 recovery rate、repair success rate、failure before/after distribution 和 repair trace。

## English Resume Version

- Extended a multimodal evidence-graph Agentic RAG system into a failure-aware self-correcting agent with diagnosis, repair policy, repair trace, and reliability evaluation.
- Designed an evidence sufficiency scorer that combines answer-term hit, citation-type match, claim support, graph context, OCR confidence, and visual grounding signals with guardrails against unsupported answers.
- Implemented a repair policy engine that maps retrieval miss, graph miss, citation mismatch, and unsupported claims to executable repair actions such as query rewrite, node-type expansion, graph-depth expansion, citation reranking, and conservative answer rewriting.
- Built a curated reliability benchmark and report comparing baseline and self-correcting strategies with recovery rate, repair success rate, before/after failure distribution, and per-case repair traces.

