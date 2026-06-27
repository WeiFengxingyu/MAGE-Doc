# MAGE-Doc Product Demo Polish 设计文档

## 1. 目标

本阶段目标不是继续增加研究型能力，而是把 V0-V3 已有能力收束成一个面试和产品展示都清晰的主线 Demo：

> 上传/准备长文档 -> 运行可信问答 -> 展示自修复过程 -> 导出可交付 Markdown 报告。

同时补充几个真实产品感功能，使项目从“模块集合”变成“可讲、可用、可交付”的产品原型。

## 2. 范围

### 2.1 产品级主线 Demo

主线体验：

1. 用户上传或选择 demo PDF。
2. 点击 `Prepare demo` 完成解析。
3. 在 V3 Repair Trace 面板输入问题。
4. 系统执行 self-correcting QA。
5. 前端展示：
   - answer。
   - citations。
   - initial/final sufficiency。
   - diagnosis。
   - repair rounds。
6. 用户导出可信问答报告。

新增一键演示体验：

1. 用户在 Product Demo Panel 输入或使用默认问题。
2. 点击 `Run interview demo`。
3. 前端自动检查文档状态，必要时先调用 `prepare-demo`。
4. 前端调用 `trusted-demo`，一次性完成 self-correcting QA 和报告生成。
5. 面板展示答案、最终充分性、修复轮次、引用数量、stop reason 和 Markdown 预览。
6. 用户可直接下载 Markdown 报告。

### 2.2 真实产品感小功能

本阶段实现最有面试展示价值的两个功能：

- **Markdown Answer Report Export**：把答案、引用、自修复过程、充分性评分和 trace 导出为 Markdown。
- **Product Demo Summary Panel**：在 Workbench 中用产品化语言展示当前文档的 demo readiness、核心能力和下一步动作。
- **One-click Interview Demo Runner**：把 prepare、trusted QA、self-correction、report preview 和 report download 收束成一个面试按钮。

## 3. 非目标

- 不接入真实外部 LLM/VLM。
- 不做复杂权限、团队协作或多租户。
- 不把导出做成 PDF 排版系统；Markdown 足够作为可信问答报告。
- 不引入新的数据库模型，避免偏离产品收口目标。

## 4. 后端设计

新增 service：

```text
backend/app/services/v3_report_export.py
```

核心函数：

- `generate_trusted_answer_report(payload: dict) -> dict`

新增 API：

```text
POST /api/v3/reports/trusted-answer
POST /api/v3/documents/{document_id}/trusted-demo
```

请求复用前端已有 self-correcting response：

```json
{
  "title": "Trusted Answer Report",
  "question": "...",
  "response": {}
}
```

响应：

```json
{
  "filename": "trusted-answer-report.md",
  "markdown": "# Trusted Answer Report\n...",
  "summary": {
    "final_sufficiency": "sufficient",
    "repair_round_count": 1,
    "citation_count": 2
  }
}
```

组合型 demo API：

```json
{
  "question": "...",
  "max_repair_rounds": 2,
  "report_title": "Trusted Answer Report"
}
```

该接口把 self-correcting QA 和报告生成打包成一条产品级主线，适合面试演示、API 文档展示和自动化 smoke test。

## 5. 前端设计

新增或修改：

```text
frontend/components/product-demo-panel.tsx
frontend/components/repair-trace-panel.tsx
frontend/lib/api.ts
frontend/types/api.ts
frontend/app/globals.css
```

说明：`frontend/app/actions.ts` 复用现有 V3 self-correcting action，本阶段不新增 server action。

前端能力：

- Product Demo Panel：
  - 显示 demo story。
  - 显示 document readiness。
  - 显示核心能力：Evidence Graph、Self-Correction、Citation、Export Report。
  - 提供 `Run interview demo`，串联 `prepareDemo` 和 `trusted-demo` API。
  - 展示 one-click result、最终 sufficiency、repair count、citation count、stop reason、report preview。
- Repair Trace Panel：
  - 保留现有 V3 repair trace。
  - 新增导出报告按钮。
  - 显示 Markdown 预览摘要。
  - 提供浏览器下载 `.md` 文件。

## 6. 验收

- 后端报告 API 可返回 Markdown。
- Markdown 至少包含 answer、citations、sufficiency、diagnosis、repair rounds、tool trace。
- 前端 build 通过。
- Product Demo Panel 可一键运行主线 Demo，并在同一面板展示报告预览和下载入口。
- 后端全量测试通过。
- README 顶部能清楚展示项目核心亮点和产品主线。
- 工作日志记录最终闭环。
