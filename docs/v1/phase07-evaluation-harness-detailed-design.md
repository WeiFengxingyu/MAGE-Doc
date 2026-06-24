# V1 Phase 7 详细设计：Evaluation Harness

## 1. Phase 目标

Phase 7 的目标是为 MAGE-Doc 建立可自动化运行的评测闭环，让项目不只“能演示”，还可以量化说明 V1 相比 V0 baseline 的改进。

本阶段新增：

- eval case schema。
- 内置小型 synthetic PDF fixture。
- strategy runner。
- metrics calculation。
- markdown/json report output。
- 后端测试覆盖 runner 和指标。

## 2. 非目标

- 不下载外部公开 PDF。
- 不做大规模 benchmark。
- 不接入外部 LLM judge。
- 不追求最终论文级评测严谨性。

## 3. 评测策略

Phase 7 先实现 2 条策略：

| 策略 | 说明 |
| --- | --- |
| `v0_agent_baseline` | 使用现有 `/questions` deterministic Agent，验证答案、引用和 claim verification |
| `v1_evidence_pack` | 使用 `/evidence-pack`，验证 source candidates、expanded evidence 和 graph context |

后续可扩展：

- `hybrid_no_graph`
- `graph_expansion_only`
- `full_v1_agent`

## 4. 数据集设计

新增目录：

```text
eval/
  cases/sample_cases.jsonl
  run_eval.py
  README.md
```

case schema：

```json
{
  "id": "sample_table_revenue_2026",
  "question": "What was revenue in 2026?",
  "question_type": "table_lookup",
  "expected_answer_terms": ["Revenue", "128", "2026"],
  "expected_node_types": ["table"],
  "expected_claim_status": "supported"
}
```

## 5. Fixture 策略

Runner 内部使用 PyMuPDF 生成 synthetic PDF：

- page 1：正文和表格。
- page 2：风险因素文本。

这样评测不依赖外部文件，CI 和本地都能稳定运行。

## 6. Metrics

输出指标：

| 指标 | 说明 |
| --- | --- |
| `answer_term_hit_rate` | expected answer terms 是否出现在答案中 |
| `citation_node_type_hit_rate` | citation node type 是否命中预期 |
| `claim_supported_rate` | claim verification 是否 supported/partial |
| `evidence_pack_context_hit_rate` | evidence pack 是否包含预期 node type |
| `average_tool_calls` | 平均工具调用数 |
| `average_latency_ms` | 平均延迟 |

## 7. CLI 设计

运行：

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v1_eval_report.json
```

输出：

- JSON report。
- Markdown report。

## 8. 测试策略

新增测试：

- runner 可以加载 sample cases。
- runner 可以生成 synthetic PDF 并准备 demo。
- `v0_agent_baseline` 产出 answer/citation/claim metrics。
- `v1_evidence_pack` 产出 evidence pack metrics。

## 9. 验收标准

- `pytest backend/app/tests/test_eval_harness.py` 通过。
- `python eval/run_eval.py --output ...` 可运行。
- 全量后端测试通过。
- 生成的 report 可放入 README。

## 10. 风险与取舍

| 风险 | 影响 | 取舍 |
| --- | --- | --- |
| synthetic case 太简单 | 指标说服力有限 | Phase 7 先保证自动化闭环，后续可替换公开 PDF |
| runner 依赖 FastAPI TestClient | 与生产调用不同 | 便于稳定测试，Phase 7 更看重本地可重复 |
| 指标不够丰富 | 简历表达有限 | 保留 JSON/Markdown 输出，为后续扩展更多指标 |
