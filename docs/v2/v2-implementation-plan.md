# MAGE-Doc V2 分阶段实现计划

## 1. 大阶段定义

V2 对应：

```text
Version: V2
Batch: Batch 3 - Advanced Multimodal Agent Platform
```

Batch 3 的目标是在 V1 已闭环的基础上，增加前沿平台化能力：

1. 扫描页 OCR。
2. 图表/视觉 grounding。
3. metric graph。
4. 多文档 collection。
5. MCP Server。
6. benchmark adapter。
7. failure diagnosis。
8. V2 release polish。

## 2. 固定工作流

每个 V2 Phase 继续遵守：

1. 先写详细设计文档。
   - 命名：`docs/v2/phaseXX-<name>-detailed-design.md`
2. 更新 V2 大阶段工作日志。
   - 文件：`docs/v2/batch3-worklog.md`
3. 按详细设计实现。
4. 运行相关测试、构建或 smoke check。
5. 更新 README、路线图或工作日志。

## 3. V2 Phase 划分

| Phase | 名称 | 核心目标 | 详细设计文档 |
| --- | --- | --- | --- |
| Phase 1 | OCR Substrate | 扫描页检测、OCR adapter、OCR text evidence nodes | `docs/v2/phase01-ocr-substrate-detailed-design.md` |
| Phase 2 | Vision Grounding | figure/chart 区域、caption/near text、visual summary adapter | `docs/v2/phase02-vision-grounding-detailed-design.md` |
| Phase 3 | Metric Graph | metric/year/entity/value 抽取与 derived evidence | `docs/v2/phase03-metric-graph-detailed-design.md` |
| Phase 4 | Multi-Document Collection | collection 模型、跨文档检索和引用 | `docs/v2/phase04-multi-document-collection-detailed-design.md` |
| Phase 5 | MCP Tool Server | 将 MAGE-Doc 工具暴露给外部 Agent | `docs/v2/phase05-mcp-tool-server-detailed-design.md` |
| Phase 6 | Benchmark Adapter | benchmark case/submission adapter 和扩展 eval report | `docs/v2/phase06-benchmark-adapter-detailed-design.md` |
| Phase 7 | Failure Diagnosis | 对 retrieval/citation/claim/OCR/vision 失败自动归因 | `docs/v2/phase07-failure-diagnosis-detailed-design.md` |
| Phase 8 | V2 Release Polish | V2 workbench、runbook、README、简历 bullets 和报告 | `docs/v2/phase08-v2-release-polish-detailed-design.md` |

## 4. Phase 1：OCR Substrate

状态：已完成。

目标：

- 检测文本密度低的扫描页。
- 增加 OCR adapter 接口。
- 支持 mock OCR fixture，保证无外部 runtime 时测试可跑。
- 创建 `ocr_text_block` evidence nodes。
- OCR bbox 能在 PDF 坐标系内引用。

验收：

- synthetic scanned-like PDF 能触发 OCR pipeline。
- OCR text node 能被 search/evidence pack 检索。
- OCR run 有 confidence 和 metadata。

## 5. Phase 2：Vision Grounding

状态：已完成。

目标：

- 增加 figure/chart candidate 节点。
- 绑定 caption 和 near text。
- 增加 visual summary adapter。
- 图表问题能引用 figure/chart/visual_summary。

验收：

- API 能列出 figure/chart evidence。
- evidence pack 能包含 visual context。
- claim verification 能识别 visual evidence citation。

## 6. Phase 3：Metric Graph

状态：已完成。

目标：

- 从表格和文本抽取 metric、year、entity、value。
- 建立 `metric_value` 节点和 `derived_from` 边。
- 支持简单差值、同比和趋势解释。

验收：

- Revenue 2025/2026 这类指标能形成 metric graph。
- metric query 能召回 metric_value 和来源 table_cell。
- 计算结果保留 derived evidence。

## 7. Phase 4：Multi-Document Collection

状态：已完成。

目标：

- 新增 collection 模型。
- 文档加入/移出 collection。
- collection-level search/evidence pack/ask。
- 引用包含 document filename。

验收：

- 两份文档可被同一问题跨文档检索。
- 答案 citations 包含 document_id、filename、page_number、bbox。

## 8. Phase 5：MCP Tool Server

状态：已完成。

目标：

- 将核心工具暴露给外部 Agent。
- 最小工具包括 search、inspect_page、read_table、build_evidence_pack、verify_claims。
- 提供本地 smoke client。

验收：

- MCP server 可启动。
- Smoke client 可调用至少 3 个工具。
- 工具输出与内部 API 一致。

## 9. Phase 6：Benchmark Adapter

状态：已完成。

目标：

- 扩展 V1 eval harness。
- 支持 benchmark-style case import/export。
- 支持 TREC/RAG 风格 submission JSON。

验收：

- JSONL benchmark case 可转换为内部 case。
- 内部结果可导出为 submission。
- report 包含 strategy metrics 和 failure summary 入口。

## 10. Phase 7：Failure Diagnosis

状态：已完成。

目标：

- 对失败 case 自动分类。
- 输出 failure diagnosis report。
- 诊断类型包括 retrieval miss、graph miss、citation mismatch、unsupported claim、OCR low confidence、visual grounding missing。

验收：

- eval report 中有 failure distribution。
- 每个 failed case 有 diagnosis reason。

## 11. Phase 8：V2 Release Polish

状态：已完成。

目标：

- Workbench 展示 OCR/vision/collection/MCP/eval 状态。
- V2 demo runbook。
- README 和简历 bullets。
- 最终测试和提交。

验收：

- V2 demo 5 到 8 分钟可讲。
- README 清晰区分 V0/V1/V2。
- 后端测试和前端 build 通过。

## 12. V2 完成定义

V2 完成必须满足：

- Phase 1 到 Phase 8 均有详细设计、实现记录和验证记录。
- OCR、vision、collection、MCP、benchmark adapter、failure diagnosis 至少各有一个可运行 smoke 或测试。
- V2 runbook、README、eval/failure report 更新。
- 本地和 GitHub 提交同步。
