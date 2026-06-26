# V2 Phase 1 详细设计：OCR Substrate

## 1. Phase 目标

Phase 1 的目标是建立扫描页 OCR 底座，让 MAGE-Doc 能把扫描页或低文本密度页面转成可检索、可引用、可进入 evidence graph 的 `ocr_text_block` 节点。

本阶段采用 adapter-first 设计，不强制安装外部 OCR runtime。

## 2. 非目标

- 不训练 OCR 模型。
- 不强制依赖 Tesseract、PaddleOCR 或 EasyOCR。
- 不处理复杂手写体。
- 不做 OCR 版面重建，只保存 block text、bbox、confidence 和 metadata。

## 3. 数据模型

新增 `ocr_runs`：

| 字段 | 说明 |
| --- | --- |
| `id` | OCR run id |
| `document_id` | 所属文档 |
| `page_id` | 页面 |
| `page_number` | 页码 |
| `status` | completed / skipped / failed |
| `adapter` | mock / external |
| `text_block_count` | OCR block 数 |
| `average_confidence` | 平均 confidence |
| `metadata_json` | 扫描页检测结果、错误等 |
| `created_at` | 创建时间 |

新增 node type：

- `ocr_text_block`

## 4. Scanned Page Detector

规则：

- 页面已有 text_block 数量为 0，视为 scanned candidate。
- 或页面 text 字符数小于阈值，视为 low-text candidate。

Phase 1 默认阈值：

```text
min_text_chars = 20
```

## 5. OCR Adapter

接口：

```python
class OcrAdapter:
    def recognize(page, page_image_path) -> list[OcrBlock]:
        ...
```

默认 mock adapter：

- 从 page metadata 或 fixture metadata 读取 `mock_ocr_blocks`。
- 如果没有 fixture，则生成稳定 fallback block：`OCR text unavailable for page N`。

## 6. API

新增：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/api/documents/{document_id}/ocr` | 对文档运行 OCR substrate |
| `GET` | `/api/documents/{document_id}/ocr-runs` | 查看 OCR run |
| `GET` | `/api/documents/{document_id}/ocr-text-blocks` | 查看 OCR evidence nodes |

## 7. 测试策略

- synthetic scanned-like PDF 可触发 OCR。
- OCR run 记录 completed。
- 生成 `ocr_text_block` evidence node。
- search 能检索 OCR 文本。
- evidence pack 能包含 OCR node。

## 8. 验收标准

- Phase 1 详细设计存在。
- OCR API、模型、服务和测试完成。
- 后端相关测试通过。
- 工作日志更新。
