# MAGE-Doc Product Demo Polish 实施计划

## 1. 阶段定义

本阶段定位：

```text
Product Demo Polish：产品级主线 Demo + 真实产品感功能
```

目标：

- 强化面试 3 分钟可理解的产品主线。
- 将 V3 self-correcting QA 变成可交付报告。
- 增强前端产品感和 README 表达。

## 2. 任务划分

| Step | 名称 | 内容 | 验收 |
| --- | --- | --- | --- |
| Step 1 | 设计文档 | 产品 Demo 设计和计划 | 文档存在并进入 README |
| Step 2 | Report Export API | Markdown report service + `/api/v3/reports/trusted-answer` | API 测试通过 |
| Step 3 | Product Demo Panel | Workbench 增加产品主线面板 | 前端 build 通过 |
| Step 4 | Report Export UI | Repair Trace 面板增加导出和预览 | 前端 build 通过 |
| Step 5 | Docs Polish | README 顶部 highlights、demo flow、工作日志 | 文档可读 |
| Step 6 | Final Verification | 后端测试、前端 build、提交推送 | main 与 origin/main 同步 |

## 3. 实现原则

- 不引入外部服务。
- 不新增数据库表。
- 复用 V3 self-correcting response。
- 把产品故事放到 README 顶部，技术细节放到版本文档。
- 所有新增能力必须有测试或构建验证。

## 4. 完成定义

完成必须满足：

- 产品 Demo 设计和计划文档存在。
- Workbench 展示产品主线 Demo。
- V3 repair trace 可导出 Markdown 报告。
- README 顶部有 core highlights 和 demo flow。
- 后端全量测试通过。
- 前端 production build 通过。
- GitHub 已同步。

