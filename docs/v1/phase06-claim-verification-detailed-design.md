# V1 Phase 6 详细设计：Claim Verification

## 1. Phase 目标

Phase 6 的目标是把答案从“带 citations 的文本”升级为 **claim-level verification**。

V0/V1 前五个阶段已经能完成：

- hybrid retrieval。
- evidence graph。
- evidence pack。
- tool trace 持久化。

Phase 6 要解决的问题是：

> 答案中的每个关键 claim 是否真的被引用证据支持？

本阶段新增：

- Claim schema。
- 规则型 claim extraction。
- Claim verifier。
- Agent 问答响应中的 `claim_verification`。
- Trace Store metadata 中记录 claim verification summary。

## 2. 非目标

- 不引入 LLM 做 claim decomposition。
- 不做自然语言蕴含模型。
- 不做复杂数学推导验证。
- 不替换原有 `verify_answer_tool`，而是在它之上增加 claim-level verifier。

## 3. Claim 状态定义

| 状态 | 含义 |
| --- | --- |
| `supported` | claim 中的关键数字、年份、实体或关键词能在引用证据中找到 |
| `partial` | 有 citation，但只覆盖部分关键信息 |
| `unsupported` | 有 citation，但证据文本无法支持 claim |
| `insufficient_evidence` | 没有 citation 或没有可用证据 |

## 4. Claim Extraction 策略

Phase 6 采用确定性规则：

1. 按句号、分号和换行切分答案。
2. 过滤太短或模板化前缀。
3. 对表格答案保留包含表格 row 的句子。
4. 每个 claim 提取：
   - numbers。
   - years。
   - keywords。
   - node type requirement。

## 5. Evidence Binding 策略

输入：

- answer。
- citations。
- optional evidence pack。

绑定策略：

- 优先使用 answer citations。
- 如果 citation node 存在于 evidence pack，则附加 evidence pack item metadata。
- 表格 claim 必须优先绑定 table/table_cell。
- 文本 claim 允许绑定 text_block、section、caption。

## 6. Verification 策略

规则：

- 没有 citations：`insufficient_evidence`。
- claim 有数字/年份，但 citation snippets 或 evidence text 缺失这些值：`partial` 或 `unsupported`。
- claim 是 table_lookup，但 citation node_type 不是 table/table_cell：`partial`。
- citation snippet 与 claim 共享关键词且关键数字匹配：`supported`。
- citation 存在但关键词几乎不重合：`unsupported`。

Verifier 输出：

```json
{
  "status": "supported",
  "claim_count": 1,
  "supported_count": 1,
  "unsupported_count": 0,
  "claims": [
    {
      "claim": "...",
      "status": "supported",
      "citation_node_ids": ["..."],
      "reason": "...",
      "matched_terms": ["Revenue", "128", "2026"],
      "missing_terms": []
    }
  ]
}
```

## 7. API 与响应设计

`POST /api/documents/{document_id}/questions` 响应新增：

- `claim_verification`

保持兼容：

- `verification` 仍保留原 `verify_answer_tool` 结果。
- `trace` 仍保留 tool trace 数组。
- `trace_id` 继续保留。

新增工具 trace：

- `verify_claims`

## 8. Trace Store 接入

Phase 6 在 trace run metadata 中记录：

- `claim_verification_status`
- `claim_count`
- `unsupported_count`

并将 `verify_claims` 作为一个 tool call 持久化。

## 9. 文件变更

新增：

- `backend/app/schemas/claim_verification.py`
- `backend/app/services/claim_verification.py`
- `backend/app/tests/test_claim_verification.py`

修改：

- `backend/app/schemas/agent.py`
- `backend/app/services/agent.py`
- `backend/app/services/tool_registry.py`
- `frontend/types/api.ts`

## 10. 测试策略

新增测试：

- 表格答案 claim 被 table citation 支持。
- 文本答案 claim 被 text citation 支持。
- 无 citation 答案标记 `insufficient_evidence`。
- 人为错配数字时标记 `partial` 或 `unsupported`。
- Agent 问答响应包含 `claim_verification`，trace 中包含 `verify_claims`。

## 11. 验收标准

- `pytest backend/app/tests/test_claim_verification.py` 通过。
- `pytest backend/app/tests/test_agent.py backend/app/tests/test_trace_store.py` 通过。
- 全量后端测试通过。
- 前端 build 通过。
- README、V1 计划、Batch 2 工作日志更新 Phase 6 状态。
- 本地 commit 完成。

## 12. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| 规则型 claim extraction 粗糙 | claim 粒度不完美 | V1 先保证可解释和可测试，后续可替换 LLM/NLI |
| 表格 row 文本和 answer 格式差异 | 数字匹配误判 | 数字/年份优先，其次关键词 overlap |
| unsupported 判断过严 | 正确答案被降级 | 使用 partial 作为中间状态，避免过度否定 |
