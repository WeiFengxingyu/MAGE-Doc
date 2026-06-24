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


def _sample_pdf_bytes() -> bytes:
    pdf = fitz.open()
    first = pdf.new_page(width=360, height=320)
    first.insert_text((60, 30), "1. Financial Highlights")
    first.insert_text((60, 50), "Revenue increased in 2026.")
    first.insert_text((60, 95), "Enterprise demand improved.")
    second = pdf.new_page(width=360, height=320)
    second.insert_text((60, 50), "Risk factors include supply chain delays.")
    return pdf.tobytes()


def _draw_table(page: fitz.Page, x0: float, y0: float) -> None:
    col_widths = [80, 80]
    row_heights = [26, 26]
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
    values = [["Metric", "2026"], ["Revenue", "128"]]
    for row_index, row in enumerate(values):
        for col_index, text in enumerate(row):
            page.insert_text((xs[col_index] + 6, ys[row_index] + 17), text, fontsize=10)


def _layout_pdf_bytes() -> bytes:
    pdf = fitz.open()
    page = pdf.new_page(width=420, height=360)
    page.insert_text((60, 30), "1. Financial Highlights")
    page.insert_text((60, 65), "Table 1. Revenue summary")
    _draw_table(page, 60, 90)
    page.insert_text((60, 170), "Revenue increased due to enterprise demand.")
    return pdf.tobytes()


def _upload_and_parse(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("graph.pdf", _sample_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    return document


def _upload_parse_tables(client: TestClient) -> dict:
    response = client.post(
        "/api/documents",
        files={"file": ("layout.pdf", _layout_pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()
    assert client.post(f"/api/documents/{document['id']}/render").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-text").status_code == 200
    assert client.post(f"/api/documents/{document['id']}/parse-tables").status_code == 200
    return document


def test_build_graph_is_idempotent_and_lists_edges(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        nodes = client.get(f"/api/documents/{document['id']}/text-blocks").json()

        first_response = client.post(f"/api/documents/{document['id']}/graph/build")
        assert first_response.status_code == 200
        first_payload = first_response.json()
        assert first_payload["node_count"] >= len(nodes)
        assert first_payload["edge_type_counts"]["contains"] >= len(nodes)
        assert first_payload["edge_type_counts"]["next"] == len(nodes) - 1
        assert first_payload["created_edge_count"] >= (len(nodes) * 2) - 1

        second_response = client.post(f"/api/documents/{document['id']}/graph/build")
        assert second_response.status_code == 200
        second_payload = second_response.json()
        assert second_payload["edge_count"] == first_payload["edge_count"]
        assert second_payload["created_edge_count"] == 0

        graph_response = client.get(f"/api/documents/{document['id']}/graph")
        assert graph_response.status_code == 200
        graph = graph_response.json()
        assert graph["node_count"] >= len(nodes)
        assert len(graph["edges"]) == first_payload["edge_count"]
        assert {"contains", "next"}.issubset({edge["edge_type"] for edge in graph["edges"]})
    finally:
        _reset_client()


def test_layout_graph_adds_sections_cells_captions_and_near_edges(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_parse_tables(client)
        response = client.post(f"/api/documents/{document['id']}/graph/build")
        assert response.status_code == 200
        payload = response.json()
        assert payload["edge_type_counts"]["part_of"] >= 4
        assert payload["edge_type_counts"]["caption_of"] >= 1
        assert payload["edge_type_counts"]["near"] >= 1

        graph = client.get(f"/api/documents/{document['id']}/graph").json()
        node_types = {node["node_type"] for node in graph["nodes"]}
        assert {"section", "table_cell", "caption"}.issubset(node_types)
        edge_types = {edge["edge_type"] for edge in graph["edges"]}
        assert {"part_of", "caption_of", "near"}.issubset(edge_types)
    finally:
        _reset_client()


def test_graph_neighbors_returns_incoming_and_outgoing_nodes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.settings.upload_root", tmp_path / "uploads")
    monkeypatch.setattr("app.services.pages.settings.page_image_root", tmp_path / "page-images")
    client = _client(tmp_path)
    try:
        document = _upload_and_parse(client)
        nodes = client.get(f"/api/documents/{document['id']}/text-blocks").json()
        assert client.post(f"/api/documents/{document['id']}/graph/build").status_code == 200

        middle_node_id = nodes[1]["id"]
        response = client.get(f"/api/documents/{document['id']}/graph/neighbors/{middle_node_id}")
        assert response.status_code == 200
        payload = response.json()

        assert payload["node"]["id"] == middle_node_id
        assert any(edge["edge_type"] == "contains" for edge in payload["incoming_edges"])
        assert any(edge["edge_type"] == "next" for edge in payload["incoming_edges"])
        assert any(edge["edge_type"] == "next" for edge in payload["outgoing_edges"])
        assert any(node["id"] == nodes[0]["id"] for node in payload["incoming_nodes"])
        assert any(node["id"] == nodes[2]["id"] for node in payload["outgoing_nodes"])
    finally:
        _reset_client()
