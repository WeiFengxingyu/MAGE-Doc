# Phase 8 Detailed Design: V0 Demo Polish 与一键准备

## 1. Phase 目标

Phase 8 将 V0 从“多个分散阶段按钮”打磨成可演示的完整工作流。用户上传 PDF 后，可以一键执行页面渲染、文本解析和表格解析，然后直接提问、查看引用、点击 citation 高亮页面证据。

核心演示链路：

```text
Upload PDF -> Prepare demo -> Ask -> View citations -> Click citation -> Highlight bbox
```

## 2. 非目标

- 不新增 LLM 能力。
- 不做后台任务队列。
- 不做复杂进度条。
- 不做持久化问答历史。
- 不做多文档集合。
- 不做生产级 job retry。

## 3. 用户可见结果

- 文档卡片提供 `Prepare demo` 操作。
- `Prepare demo` 会串行执行：
  - render pages
  - parse text blocks
  - parse tables
- 前端显示文档是否 demo ready。
- 工作台文案从 Phase 7 更新为 V0 Demo Ready。
- README 增加 V0 demo runbook。

## 4. 后端设计

新增 service：

- `backend/app/services/pipeline.py`

核心函数：

- `prepare_document_demo(db, document_id)`
  - 调用 `render_document_pages`
  - 调用 `parse_document_text_blocks`
  - 调用 `parse_document_tables`
  - 统计 pages/text_blocks/tables
  - 更新 document status 为 `demo_ready`
  - 返回 pipeline summary 和 trace

新增 API：

```text
POST /api/documents/{document_id}/prepare-demo
```

响应：

```json
{
  "document_id": "uuid",
  "status": "demo_ready",
  "page_count": 1,
  "text_block_count": 3,
  "table_count": 1,
  "steps": [
    { "name": "render_pages", "status": "ok", "output_summary": "1 pages" }
  ]
}
```

## 5. 前端设计

### 5.1 Document card

新增：

- `Prepare demo` button。
- `demo_ready` status style。

保留已有 Render/Parse buttons，方便 debug。

### 5.2 Workbench polish

新增：

- `demo-ready-panel`：当 active document 处于 demo_ready 时显示简洁提示。
- Ask placeholder 使用 demo 问题：`What was revenue in 2026?`
- System panel 当前范围改为 `V0 demo ready workflow`。

### 5.3 Runbook

新增：

- `docs/v0/v0-demo-runbook.md`

内容：

1. Start backend。
2. Start frontend。
3. Upload PDF。
4. Click Prepare demo。
5. Ask question。
6. Click citation。
7. Verify page bbox highlight and trace。

## 6. 数据与状态设计

Document status 新增：

- `preparing_demo`
- `demo_ready`

V0 继续使用单状态字段。后续版本可拆成 pipeline step 状态。

## 7. 测试和验收标准

后端测试：

- 上传生成 PDF。
- 调用 `prepare-demo`。
- 返回 `demo_ready`。
- 返回 page/text/table counts。
- 状态 API 返回 `demo_ready`。
- prepare 后可以直接调用 `/questions` 得到 citation。

前端验证：

- TypeScript 构建通过。
- DocumentRecord status 支持 `preparing_demo` 和 `demo_ready`。
- Document card 有 `Prepare demo` action。
- README 和 runbook 链接完整。

Smoke：

- 生成测试 PDF。
- upload -> prepare-demo -> ask。
- 输出 status、counts、answer、citation count。

## 8. 风险和取舍

- Prepare demo 是同步请求，大文档可能耗时较长。V0 接受，后续可引入 job queue。
- prepare 会重新渲染/解析并覆盖旧 evidence，便于 demo 稳定。
- 单状态字段会覆盖 `parsed`/`tables_parsed`，V0 用 `demo_ready` 表示最终演示态。

## 9. 完成定义

- Phase 8 详细设计完成。
- Demo runbook 完成。
- 后端 prepare-demo API、service、测试完成。
- 前端 prepare demo action、status、polish 完成。
- 后端测试通过。
- 前端构建通过。
- Smoke 通过。
- README 和 Batch 1 工作日志更新。
- 提交并推送 GitHub。
