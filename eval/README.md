# MAGE-Doc Evaluation Harness

Run the local V1 evaluation harness:

```powershell
backend\.venv\Scripts\python.exe eval\run_eval.py --output eval\reports\v1_eval_report.json
```

The runner creates a synthetic PDF fixture, uploads it through the FastAPI app, prepares the demo pipeline, runs V0/V1 strategies, and writes JSON plus Markdown reports.
