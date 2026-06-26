# MAGE-Doc V2 Batch 3 工作日志

## 2026-06-26：V2 规划启动

### 当前阶段

Batch 3 - Advanced Multimodal Agent Platform planning。

### 用户要求

- 在 V1 完整闭环后，按同样流程开始 V2 开发。
- 继续保持“详细设计 -> 实现 -> 验证 -> 工作日志”的节奏。

### 当前基线

V1 已完成：

- Evidence Graph。
- Hybrid Retrieval。
- Evidence Pack。
- Tool Registry 和 Trace Store。
- Claim Verification。
- Evaluation Harness。
- Workbench Polish。

### V2 关键决策

- V2 作为前沿增强版本，不重写 V1，而是复用 V1 的 evidence graph、trace、claim verification 和 eval harness。
- V2 先从可本地闭环的 OCR substrate 开始，不把外部 OCR/vision runtime 作为硬依赖。
- Vision、MCP、benchmark adapter 都采用 adapter-first 设计，保证没有外部服务时测试仍可运行。
- V2 仍以可观测、可验证、可评测为核心，不做不可解释的功能堆叠。

### 本次产出

- `docs/v2/v2-outline-design.md`：V2 概要设计。
- `docs/v2/v2-implementation-plan.md`：V2 分阶段实现计划。
- `docs/v2/batch3-worklog.md`：V2 大阶段工作日志。

### V2 Phase 初始划分

| Phase | 名称 | 状态 |
| --- | --- | --- |
| Phase 1 | OCR Substrate | 待开始 |
| Phase 2 | Vision Grounding | 待开始 |
| Phase 3 | Metric Graph | 待开始 |
| Phase 4 | Multi-Document Collection | 待开始 |
| Phase 5 | MCP Tool Server | 待开始 |
| Phase 6 | Benchmark Adapter | 待开始 |
| Phase 7 | Failure Diagnosis | 待开始 |
| Phase 8 | V2 Release Polish | 待开始 |

### 下一步

进入 V2 Phase 1：

1. 新建 `docs/v2/phase01-ocr-substrate-detailed-design.md`。
2. 明确 scanned-page detector、OCR adapter、OCR run model、`ocr_text_block` 节点和测试策略。
3. 实现 OCR substrate。
4. 验证 OCR node 能进入 search/evidence pack。
