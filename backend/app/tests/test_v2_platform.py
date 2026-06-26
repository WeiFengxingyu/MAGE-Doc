import importlib.util
from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app


ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_ADAPTER = ROOT / "eval" / "benchmark_adapter.py"


def _client(tmp_path: Path) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'test.sqlite'}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _reset_client() -> None:
    app.dependency_overrides.clear()


def _draw_table(page: fitz.Page, x0: float, y0: float) -> None:
    col_widths = [90, 90, 90]
    row_heights = [28, 28]
    xs = [x0]
    for width in col_widths:
        xs.append(xs[-1] + width)
    ys = [y0]
    for height in row_heights:
        ys.append(ys[-1] + height)
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), color=(0, 0, 0), width=0.8)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), color=(0, 0, 0), width=0.8)
    values = [["Metric", "2025", "2026"], ["Revenue", "100", "128"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def _pdf_bytes() -> bytes:
    pdf = fitz.open()
    page = pdf.new_page(width=420, height=320)
    page.insert_text((60, 50), "Revenue increased because enterprise demand improved.")
    _draw_table(page, 60, 95)
    return pdf.tobytes()


def _upload_prepare(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("v2-platform.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/prepare-demo").status_code == 200
    return document


def _load_benchmark_adapter():
    spec = importlib.util.spec_from_file_location("magedoc_benchmark_adapter", BENCHMARK_ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_mcp_tools_and_smoke(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_prepare(client)

        tools_response = client.get("/api/v2/mcp/tools")
        assert tools_response.status_code == 200
        tool_names = {tool["name"] for tool in tools_response.json()}
        assert {"search_doc", "inspect_page", "build_evidence_pack"}.issubset(tool_names)

        call_response = client.post(
            "/api/v2/mcp/call",
            json={
                "name": "search_doc",
                "arguments": {"document_id": document["id"], "query": "revenue", "top_k": 2},
            },
        )
        assert call_response.status_code == 200
        assert call_response.json()["tool_name"] == "search_doc"
        assert call_response.json()["content"][0]["json"]["results"]

        smoke_response = client.post(f"/api/v2/mcp/smoke/{document['id']}")
        assert smoke_response.status_code == 200
        smoke = smoke_response.json()
        assert smoke["ok"] is True
        assert smoke["called_tool_count"] == 3
    finally:
        _reset_client()


def test_v2_failure_diagnosis_api() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v2/failure-diagnosis",
        json={
            "cases": [
                {
                    "id": "case-1",
                    "expected_node_types": ["table"],
                    "expected_answer_terms": ["128"],
                }
            ],
            "results": [
                {
                    "case_id": "case-1",
                    "strategy": "v2_multimodal_graph",
                    "answer_term_hit": 0.0,
                    "citation_node_type_hit": 0.0,
                    "claim_supported": 0.0,
                },
                {
                    "case_id": "case-1",
                    "strategy": "v2_multimodal_graph",
                    "answer_term_hit": 1.0,
                    "citation_node_type_hit": 1.0,
                    "claim_supported": 1.0,
                    "evidence_pack_context_hit": 1.0,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["distribution"]["retrieval_miss"] == 1
    assert payload["distribution"]["passed"] == 1


def test_benchmark_adapter_import_and_submission(tmp_path: Path) -> None:
    adapter = _load_benchmark_adapter()
    case_file = tmp_path / "cases.jsonl"
    case_file.write_text(
        '{"qid":"bench-1","query":"What was revenue?","answers":["128"],'
        '"expected_evidence":[{"node_type":"table"}],"metadata":{"question_type":"table_lookup"}}\n',
        encoding="utf-8",
    )

    cases = adapter.load_benchmark_cases(case_file)
    assert cases[0]["id"] == "bench-1"
    assert cases[0]["question"] == "What was revenue?"
    assert cases[0]["expected_node_types"] == ["table"]

    output = tmp_path / "submission.json"
    payload = adapter.export_submission(
        [
            {
                "case_id": "bench-1",
                "answer": "Revenue was 128.",
                "evidence": [{"document_id": "doc-1", "node_id": "node-1", "page_number": 1}],
            }
        ],
        output,
    )
    assert output.exists()
    assert payload["run_name"] == "magedoc_v2_benchmark_adapter"
    assert payload["results"][0]["evidence"][0]["node_id"] == "node-1"


def test_v2_status_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v2/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["batch"] == "Batch 3 - Advanced Multimodal Agent Platform"
    assert len(payload["capabilities"]) == 8
