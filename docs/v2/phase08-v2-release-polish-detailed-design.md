# V2 Phase 8 详细设计：V2 Release Polish

## 1. 目标

Phase 8 的目标是把 V2 后半段从“代码可用”整理成“简历可展示、面试可讲、演示可跑”的交付物。

交付包括：

- Workbench 展示 V2 capability status。
- V2 demo runbook。
- README 清晰区分 V0/V1/V2。
- 简历 bullets。
- eval/failure report 更新。
- 全量测试与构建通过。

## 2. Workbench 增强

新增 V2 status panel，展示：

- OCR Substrate。
- Vision Grounding。
- Metric Graph。
- Multi-Document Collection。
- MCP Tool Server。
- Benchmark Adapter。
- Failure Diagnosis。

状态来源：

```text
GET /api/v2/status
```

## 3. 文档交付

新增：

```text
docs/v2/v2-demo-runbook.md
docs/v2/v2-resume-bullets.md
eval/reports/v2_benchmark_report.json
eval/reports/v2_benchmark_report.md
```

更新：

- `README.md`
- `docs/v2/v2-implementation-plan.md`
- `docs/v2/batch3-worklog.md`

## 4. 演示路径

5 到 8 分钟 demo：

1. 上传或准备 synthetic PDF。
2. 运行 V0/V1 pipeline。
3. 展示 OCR、visual、metric、collection 能力。
4. 展示 MCP tools manifest 和 smoke。
5. 运行 benchmark adapter。
6. 展示 failure diagnosis distribution。

## 5. 验收

- V2 Phase 1 到 8 都有详细设计、实现记录、验证记录。
- 后端全量测试通过。
- 前端 production build 通过。
- README 和 runbook 能支撑简历项目表达。

