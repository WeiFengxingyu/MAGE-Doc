# V2 Phase 2 详细设计：Vision Grounding

## 1. Phase 目标

Phase 2 的目标是为图表/图片证据建立 grounding 底座，让系统能生成 `figure`、`chart`、`visual_summary` 节点，并将它们连接到 caption/near text/table。

本阶段仍采用 adapter-first，不强制外部 vision model。

## 2. 非目标

- 不做真实图像分类模型训练。
- 不做复杂 chart axis/legend 精确解析。
- 不替换 V1 claim verifier。

## 3. 节点类型

新增：

- `figure`
- `chart`
- `visual_summary`

## 4. 边类型

复用和新增：

- `near`
- `caption_of`
- `visualizes`
- `derived_from`

## 5. Vision Adapter

默认 mock adapter：

- 基于页面绘图区域或 table/caption 附近区域生成 chart candidate。
- 生成 deterministic visual summary，例如 `Visual summary for page 1 chart region`。

未来可替换为外部 vision model。

## 6. API

新增：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/api/documents/{document_id}/vision-grounding` | 运行视觉 grounding |
| `GET` | `/api/documents/{document_id}/visual-nodes` | 查看 figure/chart/visual_summary 节点 |

## 7. 测试策略

- synthetic PDF 可生成 chart/visual_summary 节点。
- graph 中存在 `visualizes` 或 `derived_from` 边。
- evidence pack 搜索 chart/figure query 能包含 visual_summary。

## 8. 验收标准

- Phase 2 详细设计存在。
- Vision grounding API、服务和测试完成。
- 后端相关测试通过。
- 工作日志更新。
