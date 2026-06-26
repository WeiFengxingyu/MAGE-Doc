# MAGE-Doc V3 分阶段实现计划

## 1. 大阶段定义

V3 对应：

```text
Version: V3
Batch: Batch 4 - Failure-Aware Self-Correcting Agentic RAG
```

Batch 4 的目标是在 V2 已闭环的平台能力上，深化可靠性：

1. Failure Taxonomy 2.0。
2. Evidence Sufficiency Scoring。
3. Repair Policy Engine。
4. Self-Correcting Agent Loop。
5. Curated Benchmark Suite。
6. Reliability Evaluation Report。
7. Workbench Repair Trace。
8. V3 Release Polish。

## 2. 固定工作流

每个 V3 Phase 继续遵守：

1. 先写详细设计文档。
   - 命名：`docs/v3/phaseXX-<name>-detailed-design.md`
2. 更新 V3 大阶段工作日志。
   - 文件：`docs/v3/batch4-worklog.md`
3. 按详细设计实现。
4. 运行相关测试、构建或 smoke check。
5. 更新 README、runbook、eval report 或工作日志。

## 3. V3 Phase 划分

| Phase | 名称 | 核心目标 | 详细设计文档 |
| --- | --- | --- | --- |
| Phase 1 | Failure Taxonomy 2.0 | 结构化 diagnosis、severity、confidence、repair candidates | `docs/v3/phase01-failure-taxonomy-detailed-design.md` |
| Phase 2 | Evidence Sufficiency Scoring | 证据充分性评分、缺失信号、推荐修复策略 | `docs/v3/phase02-evidence-sufficiency-detailed-design.md` |
| Phase 3 | Repair Policy Engine | failure reason 到 repair action 的可测试映射 | `docs/v3/phase03-repair-policy-engine-detailed-design.md` |
| Phase 4 | Self-Correcting Agent Loop | 多轮 diagnose-repair-verify agent runtime | `docs/v3/phase04-self-correcting-agent-loop-detailed-design.md` |
| Phase 5 | Curated Benchmark Suite | 真实/半真实长文档 case、labels、failure modes | `docs/v3/phase05-curated-benchmark-suite-detailed-design.md` |
| Phase 6 | Reliability Evaluation | baseline vs repaired strategy、recovery rate report | `docs/v3/phase06-reliability-evaluation-detailed-design.md` |
| Phase 7 | Workbench Repair Trace | UI 展示 repair rounds、diagnosis、action、evidence path | `docs/v3/phase07-workbench-repair-trace-detailed-design.md` |
| Phase 8 | V3 Release Polish | runbook、README、简历 bullets、最终测试和提交 | `docs/v3/phase08-v3-release-polish-detailed-design.md` |

## 4. Phase 1：Failure Taxonomy 2.0

状态：已完成。

目标：

- 扩展 V2 `v2_failure_diagnosis`。
- diagnosis 从单 reason 字符串升级为结构化对象。
- 支持 severity、confidence、signals、repair_candidates。
- 支持多标签 failure。

验收：

- 至少覆盖 retrieval miss、graph miss、citation mismatch、unsupported claim、OCR low confidence、visual grounding missing。
- 每种 failure 都能输出 repair candidate。
- 单测覆盖 pass/fail/multi-label 三类情况。

## 5. Phase 2：Evidence Sufficiency Scoring

状态：已完成。

目标：

- 新增 sufficiency scorer。
- 聚合 answer term hit、citation type hit、claim support、graph context、OCR confidence、visual evidence signals。
- 输出 score、label、missing_signals、recommended_policy。

验收：

- 支持 sufficient、partial、insufficient 三档。
- unsupported claim 会降低 score。
- visual/OCR 依赖 case 缺少对应证据时能给出 missing signal。

## 6. Phase 3：Repair Policy Engine

状态：已完成。

目标：

- 新增 repair policy service。
- 将 diagnosis 映射为 repair action。
- repair action 包含 tool plan、参数变更、成本预算和 stop rule。

验收：

- retrieval miss -> query rewrite/node type expansion。
- graph miss -> depth/edge expansion。
- citation mismatch -> citation rerank/required type filter。
- unsupported claim -> conservative answer rewrite。
- 所有 action 都可序列化写入 trace。

## 7. Phase 4：Self-Correcting Agent Loop

状态：已完成。

目标：

- 新增 self-correcting question API。
- 执行 initial run、verify、diagnose、repair、verify_again、final。
- 每轮记录 repair trace。

验收：

- 构造一个初始检索失败 case，repair 后能提升 hit 指标。
- API 返回 final answer、citations、repair_rounds、stop_reason。
- 最大 repair rounds 可配置，默认 2。

## 8. Phase 5：Curated Benchmark Suite

目标：

- 新增 curated benchmark JSONL schema。
- 准备至少 8 到 12 个 case，覆盖 text/table/OCR/visual/metric/cross-doc。
- 每个 case 有 expected node type、answer terms、failure mode label。

验收：

- Benchmark loader 能读取 curated cases。
- Case schema 校验失败时能给出明确错误。
- README 或 runbook 说明数据来源和标注规则。

## 9. Phase 6：Reliability Evaluation

目标：

- 扩展 eval harness，加入 baseline vs self-correcting strategy。
- 输出 recovery rate、repair success rate、average repair rounds、latency delta。
- 输出 failure before/after distribution。

验收：

- JSON/Markdown report 生成。
- 至少一个 case 展示 repair 前失败、repair 后通过。
- Report 保留 V2 指标并新增 V3 reliability 指标。

## 10. Phase 7：Workbench Repair Trace

目标：

- 前端展示 self-correcting run。
- 展示每轮 diagnosis、repair action、tool trace、evidence sufficiency score。
- 用户可以看到为什么系统修改检索策略。

验收：

- Workbench 有 V3 reliability panel。
- Repair round 列表能展示 reason/action/before-after score。
- 前端 build 通过。

## 11. Phase 8：V3 Release Polish

目标：

- V3 demo runbook。
- V3 resume bullets。
- README 更新 V3 状态和评测结果。
- 最终后端测试、前端 build、提交和推送。

验收：

- V3 demo 5 到 8 分钟可讲。
- 后端全量测试通过。
- 前端 production build 通过。
- GitHub 同步。

## 12. V3 完成定义

V3 完成必须满足：

- Phase 1 到 Phase 8 均有详细设计、实现记录和验证记录。
- Failure taxonomy、sufficiency scoring、repair policy、self-correcting agent、reliability eval 至少各有一个可运行测试。
- Report 能证明 self-correction 相比 baseline 有可解释提升。
- Workbench 能展示 repair trace。
- README、runbook、简历 bullets 更新。
- 本地和 GitHub 提交同步。
