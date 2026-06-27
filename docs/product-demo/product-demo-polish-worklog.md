# MAGE-Doc Product Demo Polish 工作日志

## 2026-06-27：产品化收口启动

### 当前阶段

Product Demo Polish：产品级主线 Demo + 真实产品感功能。

### 用户要求

- 做一个产品级主线 Demo。
- 补真实产品感的几个小功能。
- 先写设计及计划文档。
- 根据文档完成。
- 最后确认项目整体闭环。

### 当前基线

项目已完成：

- V0：PDF 上传、解析、检索、问答、citation 高亮。
- V1：Evidence Graph、Hybrid Retrieval、Evidence Pack、Trace、Claim Verification、Eval。
- V2：OCR、Vision Grounding、Metric Graph、Collection、MCP、Benchmark、Failure Diagnosis。
- V3：Self-Correcting Agent、Curated Benchmark、Reliability Report、Repair Trace。

### 本次目标

- 将 V0-V3 能力收束成一条产品化 demo 主线。
- 增加可信问答 Markdown 报告导出。
- 增加产品主线说明面板。
- 更新 README，让面试官能快速看懂项目价值。

### 初始产出

- `docs/product-demo/product-demo-polish-design.md`
- `docs/product-demo/product-demo-polish-plan.md`
- `docs/product-demo/product-demo-polish-worklog.md`

### 实现产出

- 新增 `backend/app/services/v3_report_export.py`，把 V3 self-correcting response 转成可信 Markdown 报告。
- 新增 `POST /api/v3/reports/trusted-answer`，支持前端或外部系统按需导出答案报告。
- 新增 `POST /api/v3/documents/{document_id}/trusted-demo`，将自修复问答和报告生成组合成一条产品级主线 API。
- 新增 `frontend/components/product-demo-panel.tsx`，在 Workbench 顶部展示 demo readiness、主线流程和关键能力。
- 增强 `frontend/components/repair-trace-panel.tsx`，支持报告导出、浏览器下载和 Markdown 预览。
- 更新 README 顶部 core highlights、product demo flow、核心 API 和产品化闭环状态。
- 增强 `frontend/components/product-demo-panel.tsx`，新增 `Run interview demo` 一键演示入口，自动执行 prepare、trusted-demo、报告预览和 Markdown 下载。

### 验证结果

- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests\test_v3_reliability.py`：2 passed。
- `backend\.venv\Scripts\python.exe -m pytest backend\app\tests`：46 passed。
- `npm run build`：Next.js production build passed。
- GitHub 同步完成后，本阶段可作为项目产品化闭环版本。

## 2026-06-27：一键面试 Demo 补强

### 用户要求

- 补一个一键演示功能。
- 完成后上传更新。
- 同步文档。

### 实现计划

- 前端类型新增 `TrustedDemoResponse`。
- 前端 API 新增 `runTrustedDemo`，调用 `/api/v3/documents/{document_id}/trusted-demo`。
- Product Demo Panel 新增 `Run interview demo` 按钮。
- 一键流程：若文档未 `demo_ready`，先调用 `prepareDemo`；随后调用 `trusted-demo`；最后展示答案摘要、最终 sufficiency、repair count、citation count、stop reason 和 Markdown 预览。
- 报告下载复用浏览器 Blob 下载，不落本地文件。
- 同步 README、产品 Demo 设计/计划和面试讲解文档。
