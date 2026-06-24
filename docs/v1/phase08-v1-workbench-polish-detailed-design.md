# V1 Phase 8 详细设计：V1 Workbench Polish

## 1. Phase 目标

Phase 8 的目标是把 V1 的深度能力包装成可演示、可截图、可写 README 的工作台体验。

本阶段重点不是新增复杂交互，而是把 V1 已实现的能力显性展示出来：

- Hybrid retrieval score breakdown。
- Agent trace id 和 tool trace。
- Claim verification 面板。
- Citation highlight 继续可用。
- V1 demo runbook。
- README 中明确 V1 闭环状态。

## 2. 非目标

- 不引入复杂图可视化库。
- 不做完整 benchmark dashboard。
- 不重构页面布局。
- 不新增登录、历史列表或多文档管理。

## 3. 前端变更

### 3.1 Ask Panel

新增展示：

- trace id。
- verification summary。
- claim verification summary。
- claim 列表：
  - claim text。
  - status。
  - reason。
  - matched terms。
  - missing terms。

### 3.2 Retrieval Panel

新增展示：

- retrieval source。
- candidate sources。
- score breakdown：
  - lexical。
  - semantic。
  - metadata。
  - hybrid。

## 4. Demo Runbook

新增：

```text
docs/v1/v1-demo-runbook.md
```

内容包含：

1. 启动后端和前端。
2. 上传 PDF。
3. Prepare demo。
4. 搜索 evidence 并查看 hybrid score。
5. 提问。
6. 查看 citations、trace、claim verification。
7. 点击 citation 高亮 PDF 区域。
8. 运行 eval harness 并查看报告。

## 5. README 更新

README 更新 V1 Phase 1-8 状态：

- V1 已形成 evidence graph -> evidence pack -> trace -> claim verification -> eval -> workbench polish 闭环。
- 列出 eval 命令。
- 列出 V1 demo runbook。

## 6. 测试策略

- 前端 TypeScript build 通过。
- 后端全量测试通过。
- eval runner smoke 通过。

## 7. 验收标准

- 问答面板能展示 claim verification。
- 检索面板能展示 hybrid score breakdown。
- README 和 runbook 可指导 5 分钟演示。
- V1 Phase 8 工作日志完成。

## 8. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| UI 展示过多信息 | 页面拥挤 | 只展示摘要和短列表，不做复杂图面板 |
| 图可视化缺失 | V1 观感略弱 | Evidence pack 和 claim verification 先通过文本面板展示 |
| Demo runbook 与代码漂移 | 后续维护成本 | runbook 只记录稳定命令和核心流程 |
