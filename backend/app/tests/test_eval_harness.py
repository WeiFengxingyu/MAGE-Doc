import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVAL_RUNNER = ROOT / "eval" / "run_eval.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("magedoc_eval_runner", EVAL_RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_eval_runner_loads_cases() -> None:
    runner = _load_runner()

    cases = runner.load_cases()

    assert len(cases) >= 2
    assert {case["question_type"] for case in cases} == {"table_lookup", "text_lookup"}


def test_eval_runner_produces_metrics(tmp_path: Path) -> None:
    runner = _load_runner()
    output = tmp_path / "report.json"

    report = runner.run_eval(output=output)

    assert output.exists()
    assert output.with_suffix(".md").exists()
    assert report["case_count"] >= 2
    assert "v0_agent_baseline" in report["metrics"]
    assert "v1_evidence_pack" in report["metrics"]
    assert report["metrics"]["v0_agent_baseline"]["claim_supported_rate"] > 0
