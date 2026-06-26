# V3 Phase 8 详细设计：V3 Release Polish

## 1. 目标

Phase 8 的目标是把 V3 Phase 5-8 整理成完整的发布材料，使项目能作为简历和面试讲解的高阶版本。

## 2. 文档交付

新增：

```text
docs/v3/v3-demo-runbook.md
docs/v3/v3-resume-bullets.md
eval/reports/v3_reliability_report.json
eval/reports/v3_reliability_report.md
```

更新：

- `README.md`
- `docs/v3/v3-implementation-plan.md`
- `docs/v3/batch4-worklog.md`
- `eval/README.md`

## 3. Demo 结构

5 到 8 分钟：

1. 展示 V3 定位：Failure-Aware Self-Correcting Agentic RAG。
2. 跑一个表格问题，展示初始 sufficiency 和 diagnosis。
3. 展示 repair action 和 final sufficiency。
4. 展示 V3 reliability report。
5. 讲 benchmark-driven 可靠性闭环。

## 4. 验收

- Phase 5-8 均有 detailed design、实现、测试、日志。
- 后端全量测试通过。
- 前端 build 通过。
- README 和 runbook 明确区分 V0/V1/V2/V3。
- GitHub 同步。

