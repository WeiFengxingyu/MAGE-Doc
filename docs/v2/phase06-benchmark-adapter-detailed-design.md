# V2 Phase 6 详细设计：Benchmark Adapter

## 1. 目标

Phase 6 的目标是把 V1 eval harness 升级为 benchmark-ready 的输入输出层，使 MAGE-Doc 能把外部 RAG 评测样例转换为内部 case，并把内部结果导出为 TREC/RAG 风格 submission。

本 phase 不承诺直接参赛，但要让项目具备参赛前的结构：

- JSONL benchmark case import。
- 内部 eval case normalization。
- submission JSON export。
- report 中包含 V2 strategy metrics 和 failure summary 入口。

## 2. 输入格式

支持 benchmark JSONL，每行一个 case：

```json
{
  "qid": "case-001",
  "query": "What was revenue in 2026?",
  "answers": ["128"],
  "doc_ids": ["magedoc-eval.pdf"],
  "expected_evidence": [{"node_type": "table"}],
  "metadata": {"question_type": "table_lookup"}
}
```

兼容内部字段：

- `id`
- `question`
- `question_type`
- `expected_answer_terms`
- `expected_node_types`

## 3. 输出格式

导出 submission：

```json
{
  "run_name": "magedoc_v2_benchmark_adapter",
  "results": [
    {
      "qid": "case-001",
      "answer": "...",
      "evidence": [
        {
          "document_id": "...",
          "node_id": "...",
          "page_number": 1,
          "bbox": [0, 0, 100, 100]
        }
      ]
    }
  ]
}
```

## 4. 实现设计

新增模块：

```text
eval/benchmark_adapter.py
```

核心函数：

- `load_benchmark_cases(path)`
- `benchmark_to_internal_case(row)`
- `export_submission(results, output, run_name)`
- `build_failure_summary(results)`

扩展：

- `eval/run_eval.py` 增加 V2 evidence graph strategy。
- report 写入 `failure_summary`。
- report markdown 增加 failure distribution。

## 5. V2 Strategy

新增 strategy：

```text
v2_multimodal_graph
```

执行方式：

1. 准备文档。
2. 运行 OCR、vision grounding、metric graph。
3. 使用 evidence pack 搜索候选。
4. 记录 evidence node type hit、answer term hit、tool calls、latency。

## 6. 验收

- benchmark JSONL 可以转换为内部 case。
- eval report 中包含 `v2_multimodal_graph`。
- submission JSON 可以写入磁盘。
- report 中包含 failure summary 字段。

