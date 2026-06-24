# MAGE-Doc 开发流程标准

## 1. 目标

MAGE-Doc 按“文档先行、分阶段闭环、实现可追踪”的方式开发。每个小 Phase 必须先写详细设计，再按设计实现、验证、记录结论。

这个流程用于避免范围失控，也保证项目最终能形成面试可讲、简历可写、代码可验的完整证据链。

## 2. 阶段层级

项目分三层推进：

```text
Version -> Batch -> Phase
```

- `Version`：大版本，例如 V0、V1、V2。
- `Batch`：一个大阶段，例如 Batch 1 = V0 Foundation。
- `Phase`：可独立设计、实现、验证的小阶段，例如 Phase 0 项目骨架。

## 3. 每个 Phase 的固定流程

每个 Phase 都按以下顺序执行：

1. **写详细设计文档**
   - 文件命名：`docs/v0/phaseXX-<name>-detailed-design.md`
   - 必须写清目标、范围、架构、文件结构、接口、验收标准和风险。

2. **更新大阶段工作日志**
   - 文件命名：`docs/v0/batch1-worklog.md`
   - 记录当前 Phase 的设计决策、实现过程、验证结果和遗留问题。

3. **按详细设计实现**
   - 严格控制范围。
   - 不提前实现后续 Phase 的复杂功能。
   - 必要的占位代码必须有清晰命名和后续替换说明。

4. **运行验证**
   - 至少运行和本 Phase 相关的测试、构建或 smoke check。
   - 如果暂时无法验证，必须在工作日志中记录原因。

5. **收尾更新**
   - 更新 README 或阶段文档索引。
   - 更新工作日志的完成状态。
   - 明确下一 Phase 的入口。

## 4. 文档规范

### 4.1 详细设计文档必须包含

- Phase 目标。
- 非目标。
- 用户可见结果。
- 技术方案。
- 目录和文件变更。
- 数据模型或 API 变更。
- 前端交互。
- 测试和验收标准。
- 风险和取舍。

### 4.2 工作日志必须包含

- 日期。
- 当前 Phase。
- 用户要求和关键决策。
- 实现摘要。
- 验证结果。
- 遗留问题。
- 下一步。

## 5. 实现原则

- 先闭环，后加深。
- 先可观测，后智能化。
- 先 bbox 证据定位，后复杂多模态推理。
- 先本地可运行，后外部服务依赖。
- 先小评测集，后大 benchmark。

## 6. 自动持续执行约定

当用户要求“继续开发”时，可以自动推进当前 Batch 的下一个 Phase，但仍必须遵守：

1. 先写该 Phase 详细设计。
2. 再实现。
3. 再验证。
4. 再记录工作日志。

如果遇到需要用户选择的高风险问题，优先给出保守默认方案并继续推进；只有在无法安全决策时才暂停询问。

## 7. V0 Phase 列表

| Phase | 名称 | 详细设计 |
| --- | --- | --- |
| Phase 0 | 项目骨架 | `docs/v0/phase00-project-skeleton-detailed-design.md` |
| Phase 1 | 文档上传与状态管理 | `docs/v0/phase01-document-upload-detailed-design.md` |
| Phase 2 | 页面渲染与坐标系统 | `docs/v0/phase02-page-rendering-coordinate-system-detailed-design.md` |
| Phase 3 | 文本块解析 | `docs/v0/phase03-text-block-parsing-detailed-design.md` |
| Phase 4 | 基础表格解析 | `docs/v0/phase04-table-parsing-detailed-design.md` |
| Phase 5 | 基础检索与工具层 | 待创建 |
| Phase 6 | V0 Agentic RAG 闭环 | 待创建 |
| Phase 7 | 前端问答与引用高亮 | 待创建 |
