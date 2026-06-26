from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app


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
    page.insert_text((60, 50), "Enterprise demand improved during the year.")
    _draw_table(page, 60, 95)
    return pdf.tobytes()


def _upload_prepare(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("v3-reliability.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/prepare-demo").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/metric-graph/build").status_code == 200
    return document


def test_v3_taxonomy_sufficiency_and_repair_plan() -> None:
    client = TestClient(app)
    taxonomy_response = client.post(
        "/api/v3/failure-taxonomy",
        json={
            "cases": [{"id": "case-1", "expected_node_types": ["table"]}],
            "results": [
                {
                    "case_id": "case-1",
                    "strategy": "v3_self_correcting_agent",
                    "answer_term_hit": 0.0,
                    "citation_node_type_hit": 0.0,
                    "claim_supported": 0.0,
                    "evidence_pack_context_hit": 0.0,
                }
            ],
        },
    )
    assert taxonomy_response.status_code == 200
    diagnosis = taxonomy_response.json()["diagnoses"][0]
    assert diagnosis["reason"] == "retrieval_miss"
    assert diagnosis["severity"] == "high"
    assert "query_rewrite" in diagnosis["repair_candidates"]

    sufficiency_response = client.post(
        "/api/v3/sufficiency-score",
        json={
            "case": {"id": "case-1", "expected_node_types": ["table"]},
            "result": {
                "answer_term_hit": 0.0,
                "citation_node_type_hit": 0.0,
                "claim_supported": 0.0,
                "evidence_pack_context_hit": 0.0,
            },
        },
    )
    assert sufficiency_response.status_code == 200
    assert sufficiency_response.json()["label"] == "insufficient"

    repair_response = client.post("/api/v3/repair-plan", json={"diagnoses": [diagnosis]})
    assert repair_response.status_code == 200
    repair_plan = repair_response.json()
    assert repair_plan["has_repair"] is True
    assert repair_plan["actions"][0]["action"] == "query_rewrite"


def test_v3_self_correcting_question_repairs_table_lookup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_prepare(client)

        response = client.post(
            f"/api/v3/documents/{document['id']}/self-correcting-questions",
            json={"question": "What was revenue in 2026?", "max_repair_rounds": 2},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["repair_round_count"] >= 1
        assert payload["final_sufficiency"]["score"] >= payload["initial_sufficiency"]["score"]
        assert payload["final_sufficiency"]["label"] in {"partial", "sufficient"}
        assert payload["citations"]
        assert payload["stop_reason"] in {
            "sufficient_after_repair",
            "max_repair_rounds_reached",
        }
        selected_actions = {round_item["selected_action"]["action"] for round_item in payload["repair_rounds"]}
        assert selected_actions & {
            "query_rewrite",
            "node_type_expansion",
            "graph_depth_expansion",
            "citation_rerank",
        }
    finally:
        _reset_client()
