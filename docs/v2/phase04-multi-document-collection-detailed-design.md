# V2 Phase 4 详细设计：Multi-Document Collection

## 1. Phase 目标

Phase 4 的目标是建立多文档 collection 底座，使 MAGE-Doc 可以在多个文档之间检索证据，并返回带 document metadata 的引用。

## 2. 非目标

- 不做权限系统。
- 不做大规模向量库。
- 不做复杂跨文档冲突消解。

## 3. 数据模型

新增：

- `collections`
- `collection_documents`

collection document membership：

- collection_id。
- document_id。
- added_at。

## 4. API

新增：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `POST` | `/api/collections` | 创建 collection |
| `GET` | `/api/collections` | 列出 collections |
| `POST` | `/api/collections/{collection_id}/documents/{document_id}` | 加入文档 |
| `GET` | `/api/collections/{collection_id}/search` | 跨文档检索 |

## 5. 检索策略

Phase 4 复用单文档 `search_evidence`：

- 遍历 collection 内文档。
- 合并 top results。
- result 中附加 document filename。
- 排序按 score、document filename、page_number。

## 6. 测试策略

- 创建 collection。
- 加入两份文档。
- collection search 能返回多个 document 的结果。
- result 包含 document metadata。

## 7. 验收标准

- Phase 4 详细设计存在。
- Collection 模型、API、服务和测试完成。
- 后端相关测试通过。
- 工作日志更新。
