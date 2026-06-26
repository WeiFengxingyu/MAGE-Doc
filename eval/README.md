# MAGE-Doc Evaluation Harness

Run the local V3 reliability evaluation harness:

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --cases eval\cases\v3_curated_cases.jsonl --output eval\reports\v3_reliability_report.json
```

The runner creates a synthetic PDF fixture, uploads it through the FastAPI app, prepares the demo pipeline, runs V0/V1/V2/V3 strategies, and writes JSON plus Markdown reports.

V2 adds:

- `v2_multimodal_graph` strategy.
- OCR, vision grounding, and metric graph preparation before evaluation.
- Failure diagnosis summary in the report.
- Benchmark adapter helpers in `eval/benchmark_adapter.py`.

V3 adds:

- Curated benchmark schema in `eval/curated_benchmark.py`.
- Curated cases in `eval/cases/v3_curated_cases.jsonl`.
- `v3_self_correcting` strategy.
- Reliability summary with recovery rate, repair success rate, repair rounds, and failure before/after distribution.
