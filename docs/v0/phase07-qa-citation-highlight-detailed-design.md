# Phase 7 Detailed Design: 前端问答与引用高亮

## 1. Phase 目标

Phase 7 完成 V0 可演示工作台的关键交互：用户在 Ask 面板获得答案后，可以点击 citation，页面 viewer 自动切换到引用所在页面，并用醒目的 bbox 高亮该证据。

本阶段把 Phase 6 的 `answer -> citations` 从静态文本升级为可定位证据体验。

## 2. 非目标

- 不新增后端 Agent 能力。
- 不做持久化问答历史。
- 不做多 citation 同时高亮。
- 不做跨文档问答。
- 不做复杂 PDF 翻页控件。
- 不做 citation URL deep link。

## 3. 用户可见结果

- Ask 面板中的 citation 变成可点击按钮。
- 点击 citation 后：
  - 页面 viewer 显示 citation 所在页。
  - citation bbox 用高亮框覆盖在页面图上。
  - viewer 顶部显示当前 selected citation 信息。
- 用户仍能看到文本块和表格 overlay。
- 无 citation 时显示空状态。

## 4. 前端状态设计

Phase 7 新增一个 client-side workbench 组件：

```text
DocumentWorkbench
  - selectedCitation
  - selectedPageNumber
  - AskPanel(onCitationSelect)
  - PageViewer(selectedCitation, selectedPageNumber, onPageSelect)
  - RetrievalPanel
```

原因：

- 当前 `app/page.tsx` 是 server component，不能直接持有交互状态。
- AskPanel 已是 client component，PageViewer 可升级为 client component。
- 用 `DocumentWorkbench` 包住 AskPanel 和 PageViewer，可以局部管理 citation highlight 状态，不影响后端和已有数据加载。

## 5. 数据加载设计

Server component 仍负责加载：

- active document。
- pages。
- first/active page 的 text blocks 和 tables。

Phase 7 为了支持页面切换，需要让 client 侧按需请求：

- `listPageTextBlocks(documentId, pageNumber)`
- `listPageTables(documentId, pageNumber)`

现有 API helper 已支持这两个接口，可在 client component 中复用。

## 6. 组件变更

### 6.1 `AskPanel`

新增 props：

- `onCitationSelect?: (citation: Citation) => void`
- `selectedCitationId?: string | null`

变更：

- citation item 从静态 article 改成 button/card。
- 点击 citation 调用 `onCitationSelect`。
- 当前选中的 citation 增加 active 样式。

### 6.2 `PageViewer`

升级为 client component。

新增 props：

- `selectedCitation?: Citation | null`
- `initialPageNumber?: number`

变更：

- 根据 selected citation 切换当前页。
- 当页码变化时加载该页 text blocks 和 tables。
- 在文本/表格 overlay 上额外绘制 selected citation highlight。
- selected citation highlight 使用独立样式，视觉优先级高于普通 overlay。

### 6.3 `DocumentWorkbench`

新增组件：

- 管理 `selectedCitation`。
- 接收 server 加载的 active document、pages、first page text blocks、first page tables。
- 组合 PageViewer、AskPanel、RetrievalPanel。

## 7. 样式设计

新增：

- `.citation-button`
- `.citation-button-active`
- `.selected-citation-bbox`
- `.selected-citation-banner`

设计原则：

- 普通 text/table overlay 仍保留。
- selected citation 用琥珀色边框和半透明背景，和普通绿色/蓝色 overlay 区分。
- 不遮挡页面内容过多。

## 8. 测试和验收标准

后端：

- Phase 7 不新增后端逻辑，但仍运行完整后端测试防回归。

前端：

- TypeScript 构建通过。
- `PageViewer` 可接收 selected citation。
- `AskPanel` citation 点击事件类型正确。
- `DocumentWorkbench` 能组合现有 server data 和 client state。

Smoke：

- 使用构建验证前端可编译。
- 通过代码检查确认：
  - citation 点击调用 `onCitationSelect`。
  - selected citation bbox 使用 page.width/page.height 换算 overlay。
  - selected citation page number 驱动页面切换。

## 9. 风险和取舍

- 当前页面切换只在 viewer 内部完成，不提供完整 pagination UI。
- citation 选中状态是 client memory，不持久化。
- 如果 citation 所在页的 evidence API 加载失败，仍显示页面图片和 citation bbox。
- 多 citation 同时高亮留到后续版本。

## 10. 完成定义

- Phase 7 详细设计完成。
- `DocumentWorkbench` 完成。
- `AskPanel` citation 可点击。
- `PageViewer` 支持 selected citation 页面切换和 bbox 高亮。
- 前端构建通过。
- 后端测试通过。
- README 和 Batch 1 工作日志更新。
