# MAGE-Doc Evaluation Harness

Run the local V2 evaluation harness:

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v2_benchmark_report.json
```

The runner creates a synthetic PDF fixture, uploads it through the FastAPI app, prepares the demo pipeline, runs V0/V1/V2 strategies, and writes JSON plus Markdown reports.

V2 adds:

- `v2_multimodal_graph` strategy.
- OCR, vision grounding, and metric graph preparation before evaluation.
- Failure diagnosis summary in the report.
- Benchmark adapter helpers in `eval/benchmark_adapter.py`.
