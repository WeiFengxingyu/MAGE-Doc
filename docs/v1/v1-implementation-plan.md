# MAGE-Doc V1 分阶段实现计划

## 1. 大阶段定义

V1 对应：

```text
Version: V1
Batch: Batch 2 - Evidence Graph Agentic RAG
```

Batch 2 的目标不是替换 V0，而是在 V0 已闭环的基础上逐层加深：

1. 把证据从“列表”升级成“图”。
2. 把检索从“单次 top-k”升级成“hybrid + graph expansion”。
3. 把 Agent 从“固定问答流程”升级成“可审计工具运行时”。
4. 把答案从“带引用文本”升级成“claim-level evidence pack”。
5. 把 demo 从“能看”升级成“有指标、有对比、有解释”。

## 2. 固定工作流

每个 V1 Phase 继续遵守 V0 的闭环标准：

1. 先写详细设计文档。
   - 命名：`docs/v1/phaseXX-<name>-detailed-design.md`
   - 必须包含目标、非目标、技术方案、数据/API 变更、前端交互、测试和验收标准。
2. 更新 V1 大阶段工作日志。
   - 文件：`docs/v1/batch2-worklog.md`
3. 根据详细设计实现。
4. 运行相关测试、构建或 smoke check。
5. 更新 README、路线图或工作日志，记录完成状态和下一 Phase 入口。

任何 Phase 都不允许跳过详细设计直接写代码。

## 3. V1 Phase 划分

| Phase | 名称 | 核心目标 | 详细设计文档 |
| --- | --- | --- | --- |
| Phase 1 | Evidence Graph 数据模型 | 新增 edge table 和 graph service，把 V0 evidence nodes 接入图结构 | `docs/v1/phase01-evidence-graph-data-model-detailed-design.md` |
| Phase 2 | Layout 关系与 Section 构建 | 构建 page/section/text/table/cell/caption 的 contains、next、near、part_of 边 | `docs/v1/phase02-layout-section-graph-detailed-design.md` |
| Phase 3 | Hybrid Retrieval Index | 引入 lexical + semantic adapter，输出统一 retrieval candidates | `docs/v1/phase03-hybrid-retrieval-index-detailed-design.md` |
| Phase 4 | Graph Expansion 与 Evidence Pack | 基于 top candidates 扩展邻域，生成 answer-ready evidence pack | `docs/v1/phase04-graph-expansion-evidence-pack-detailed-design.md` |
| Phase 5 | Tool Registry 与 Trace Store | 统一工具 schema，持久化 tool call、planner step 和执行摘要 | `docs/v1/phase05-tool-registry-trace-store-detailed-design.md` |
| Phase 6 | Claim Verification | 将答案拆成 claims，并判断 supported / partial / unsupported | `docs/v1/phase06-claim-verification-detailed-design.md` |
| Phase 7 | Evaluation Harness | 建立公开 PDF 小评测集，跑策略对比和指标报告 | `docs/v1/phase07-evaluation-harness-detailed-design.md` |
| Phase 8 | V1 Workbench Polish | 前端展示 evidence graph、trace timeline、claim verification 和 demo runbook | `docs/v1/phase08-v1-workbench-polish-detailed-design.md` |

## 4. Phase 1：Evidence Graph 数据模型

状态：已完成。

### 目标

让 V0 的 document、page、text block、table 能进入统一 evidence graph，后续所有检索和 Agent 逻辑都基于 graph service 查询。

### 主要任务

- 新增 `evidence_edges` 数据模型和迁移逻辑。
- 定义 edge type、weight、source、metadata。
- 为已有 document/page/evidence node 生成基础 `contains` 和 `next` 边。
- 新增 graph service：创建边、查询邻域、查询路径、导出子图。
- 新增 graph API，支持前端和测试读取节点邻域。

### 验收标准

- 对已解析文档可以构建基础图。
- 给定 page 能查到该页 evidence nodes。
- 给定 evidence node 能查到前后相邻节点。
- 后端测试覆盖 edge creation、neighbor query 和 idempotent graph build。

## 5. Phase 2：Layout 关系与 Section 构建

状态：已完成。

### 目标

把 PDF 的阅读顺序、章节候选、表格单元格和 caption 候选编码成图边，让 graph expansion 有可信上下文。

### 主要任务

- 基于字体、bbox、文本长度和序号规则识别 section candidate。
- 构建 section -> text_block/table 的 `contains` 边。
- 将 table matrix 拆为 `table_cell` 节点。
- 构建 table -> cell 的 `part_of` 或 `contains` 边。
- 根据空间邻近关系生成 `near` 边。
- 为 table 附近文本生成 caption candidate。

### 验收标准

- 前端或 API 能展示某页 section/block/table/cell 层级。
- 表格问题能定位到 table_cell 级别证据。
- graph export 中可看到 section、cell 和 caption 相关节点或边。

## 6. Phase 3：Hybrid Retrieval Index

状态：已完成。

### 目标

让检索不再只依赖 V0 的关键词匹配，而是支持 lexical、semantic 和 metadata-aware candidate 合并。

### 主要任务

- 定义 retrieval index service。
- 保留本地 lexical scorer。
- 新增 embedding adapter 接口。
- 提供默认本地 fallback，避免外部 API 成为运行门槛。
- 建立 `retrieval_candidates` 结构，记录来源、分数和解释。
- API 返回候选来源、score breakdown 和 matched fields。

### 验收标准

- 文本问题和表格问题都能返回 lexical 与 semantic candidate。
- 没有外部 embedding 配置时，系统仍可运行。
- 后端测试覆盖 candidate merge、score normalization 和 fallback。

## 7. Phase 4：Graph Expansion 与 Evidence Pack

状态：已完成。

### 目标

把检索候选扩展成可供回答和验证的 evidence pack，而不是直接把 top-k snippet 交给 Agent。

### 主要任务

- 对 top candidates 按 edge type 和 depth 扩展邻域。
- 支持 section context、page context、table context 和 caption context。
- 设计 evidence pack 数据结构。
- 为每个候选记录 graph distance、edge path 和 inclusion reason。
- 新增 evidence pack API 和测试。

### 验收标准

- 给定 query 可以返回 evidence pack。
- pack 中包含原始候选、扩展节点、边路径和引用元数据。
- graph expansion 有 top-k、depth 和 edge type 限制。

## 8. Phase 5：Tool Registry 与 Trace Store

状态：已完成。

### 目标

把 V0 的工具函数升级成统一注册、可审计、可回放的 Agent runtime。

### 主要任务

- 定义 tool schema、tool input、tool output 和 error contract。
- 新增 trace store，持久化 question、planner steps、tool calls 和 verifier results。
- 改造 `search_evidence`、`inspect_page`、`read_table`、`verify_answer`。
- 新增 `expand_graph` 和 `explain_trace`。
- 前端 trace panel 读取持久化 trace。

### 验收标准

- 每个问题都有唯一 trace id。
- 每个工具调用保存输入摘要、输出摘要、耗时、状态。
- 前端刷新后仍能查看历史 trace。

## 9. Phase 6：Claim Verification

状态：已完成。

### 目标

答案不只“看起来有引用”，而是每个关键 claim 都能被 evidence pack 检查。

### 主要任务

- 设计 answer claim schema。
- 从 deterministic answer composer 中输出 claims。
- 对数字、年份、实体、指标名做 evidence matching。
- 表格 claim 强制绑定 table/table_cell evidence。
- 输出 supported、partial、unsupported、insufficient_evidence。
- 前端展示 claim verification。

### 验收标准

- 答案至少包含 claim 列表和每个 claim 的 verification label。
- 引用证据缺失时，系统不会标记为 supported。
- 后端测试覆盖文本 claim、表格 claim 和 unsupported claim。

## 10. Phase 7：Evaluation Harness

状态：已完成。

### 目标

形成可以写进 README 和简历的量化对比。

### 主要任务

- 建立 `eval/` 数据目录和 JSONL schema。
- 准备 2 到 3 份公开 PDF 的小问题集。
- 实现 strategy runner：V0 baseline、hybrid no graph、graph expansion、full V1 agent。
- 计算 citation page hit、node type match、table QA、unsupported claim rate、latency。
- 输出 markdown/JSON 报告。

### 验收标准

- 一条命令可以跑完整小评测。
- 报告能显示各策略指标。
- README 可以引用核心结果。

## 11. Phase 8：V1 Workbench Polish

状态：已完成。

### 目标

把 V1 的深度能力包装成 5 分钟可演示的工作台。

### 主要任务

- Evidence graph/path 可视化。
- Trace timeline 和 tool call detail。
- Claim verification panel。
- Table cell citation view。
- V1 demo runbook。
- README 截图位和简历 bullets。

### 验收标准

- 上传公开 PDF 后可完成 V1 demo。
- 用户能看到“检索 -> 扩图 -> 读表 -> 验证 -> 引用”的完整链路。
- V1 的差异点在 README 中清晰呈现。

## 12. V1 完成定义

状态：已完成。

V1 完成必须同时满足：

- 所有 Phase 1 到 Phase 8 均有详细设计文档、实现记录和验收记录。
- 后端测试和前端构建通过。
- V1 demo runbook 可复现。
- 至少有一份评测报告。
- README 能清楚说明 V0 baseline 与 V1 evidence graph agent 的差异。
- 简历 bullet、架构图和核心截图已准备。
