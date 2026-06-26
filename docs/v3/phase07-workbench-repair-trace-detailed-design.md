# V3 Phase 7 详细设计：Workbench Repair Trace

## 1. 目标

Phase 7 的目标是在前端 Workbench 中展示 V3 self-correcting run，让用户能看到 Agent 为什么修、怎么修、修复前后证据充分性是否提升。

## 2. UI 范围

新增 V3 Repair Trace 面板：

- 输入问题。
- 调用 `/api/v3/documents/{document_id}/self-correcting-questions`。
- 展示 answer、citations、initial/final sufficiency。
- 展示 repair rounds。
- 展示每轮 diagnosis reason、selected action、before/after score。

## 3. 前端文件

新增或修改：

```text
frontend/components/repair-trace-panel.tsx
frontend/app/actions.ts
frontend/lib/api.ts
frontend/types/api.ts
frontend/components/document-workbench.tsx
frontend/app/globals.css
```

## 4. 交互

- 无文档时按钮 disabled。
- 默认问题：`What was revenue in 2026?`
- 如果没有 repair round，仍展示 final diagnosis 和 sufficiency。
- Citations 可复用现有 Citation 类型。

## 5. 验收

- Frontend production build 通过。
- Panel 不影响现有 AskPanel。
- 文本不溢出，repair round card 可扫描。

