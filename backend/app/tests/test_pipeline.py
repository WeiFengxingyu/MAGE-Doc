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
    row_heights = [28, 28, 28]
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

    values = [
        ["Metric", "2025", "2026"],
        ["Revenue", "100", "128"],
        ["Margin", "18%", "22%"],
    ]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 18), text, fontsize=10)


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    page = pdf.new_page(width=420, height=320)
    page.insert_text((60, 50), "Revenue increased because enterprise demand improved.")
    _draw_table(page, 60, 95)
    return pdf.tobytes()


def test_prepare_demo_runs_v0_pipeline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        upload_response = client.post(
            "/api/documents",
            files={"file": ("pipeline.pdf", _sample_pdf_bytes(), "application/pdf")},
        )
        assert upload_response.status_code == 201
        document = upload_response.json()

        prepare_response = client.post(f"/api/documents/{document['id']}/prepare-demo")

        assert prepare_response.status_code == 200
        payload = prepare_response.json()
        assert payload["status"] == "demo_ready"
        assert payload["page_count"] == 1
        assert payload["text_block_count"] >= 1
        assert payload["table_count"] == 1
        assert [step["name"] for step in payload["steps"]] == [
            "render_pages",
            "parse_text_blocks",
            "parse_tables",
        ]

        status_response = client.get(f"/api/documents/{document['id']}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "demo_ready"

        question_response = client.post(
            f"/api/documents/{document['id']}/questions",
            json={"question": "What was revenue in 2026?"},
        )
        assert question_response.status_code == 200
        assert question_response.json()["verification"]["passed"] is True
    finally:
        _reset_client()
