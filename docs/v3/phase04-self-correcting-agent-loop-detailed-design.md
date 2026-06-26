# V3 Phase 4 详细设计：Self-Correcting Agent Loop

## 1. 目标

Phase 4 的目标是把 V1/V2 的固定工具链 Agent 升级为可诊断、可修复、可验证的 self-correcting agent。

## 2. 默认流程

```text
initial_search
  -> evidence_pack
  -> draft_answer
  -> verify_claims
  -> sufficiency_score
  -> failure_diagnosis
  -> repair_policy
  -> repair_run
  -> final_verify
```

## 3. API

新增：

```text
POST /api/v3/documents/{document_id}/self-correcting-questions
POST /api/v3/failure-taxonomy
POST /api/v3/sufficiency-score
POST /api/v3/repair-plan
```

请求：

```json
{
  "question": "What was revenue in 2026?",
  "max_repair_rounds": 2
}
```

响应：

```json
{
  "document_id": "...",
  "question": "...",
  "answer": "...",
  "citations": [],
  "repair_rounds": [],
  "initial_sufficiency": {},
  "final_sufficiency": {},
  "stop_reason": "sufficient_after_repair"
}
```

## 4. Repair 执行策略

V3 Phase 4 先实现确定性 repair：

- `query_rewrite`：添加 table/revenue/metric 等 domain terms 或复用原 query。
- `node_type_expansion`：从 primary node type 扩展到所有 multimodal node types。
- `graph_depth_expansion`：evidence pack depth 从 1 提升到 2。
- `required_type_filter`：优先选择诊断期望的 node type。
- `conservative_answer_rewrite`：如果证据不足，输出保守答案并标记 unsupported。

## 5. Trace

每轮 repair round 记录：

- round_index。
- diagnosis。
- repair_actions。
- before_sufficiency。
- after_sufficiency。
- tool_traces。

## 6. 验收

- API 能返回 initial/final sufficiency。
- 至少一个 test case 能触发 repair round。
- repair 后的 score 不低于 repair 前。
- 最大 repair 轮数生效。

