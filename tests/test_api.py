"""Tests for the FastAPI layer."""
from __future__ import annotations

import io
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_pdf_bytes(text: str = "Total Revenue") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _make_rules_bytes(search: str = "Total Revenue") -> bytes:
    content = f"""rules:
  - name: "Tick {search}"
    type: tick
    search: "{search}"
    position: right
    match: all
"""
    return content.encode()


# --- POST /annotate ---

def test_post_annotate_returns_200(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes(), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes(), "application/x-yaml"),
        },
    )
    assert response.status_code == 200


def test_post_annotate_response_includes_marks_placed(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes("Total Revenue"), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes("Total Revenue"), "application/x-yaml"),
        },
    )
    data = response.json()
    assert "marks_placed" in data
    assert data["marks_placed"] == 1


def test_post_annotate_response_includes_job_id(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes(), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes(), "application/x-yaml"),
        },
    )
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)
    assert len(data["job_id"]) > 0


def test_post_annotate_response_includes_verification(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes("Total Revenue"), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes("Total Revenue"), "application/x-yaml"),
        },
    )
    data = response.json()
    assert "verification" in data
    v = data["verification"]
    assert "passed" in v
    assert "total_annotations" in v
    assert "rule_results" in v
    assert v["passed"] is True
    assert len(v["rule_results"]) == 1
    assert v["rule_results"][0]["status"] == "PASS"


def test_post_annotate_no_match_returns_verification_fail(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes("Hello World"), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes("NonexistentText"), "application/x-yaml"),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verification"]["passed"] is False


def test_post_annotate_invalid_pdf_returns_422(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", b"not a pdf", "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes(), "application/x-yaml"),
        },
    )
    assert response.status_code == 422


def test_post_annotate_invalid_yaml_returns_422(client: TestClient) -> None:
    response = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes(), "application/pdf"),
            "rules_file": ("rules.yaml", b": invalid: yaml: {{", "application/x-yaml"),
        },
    )
    assert response.status_code == 422


# --- GET /download/{job_id} ---

def test_get_download_returns_pdf(client: TestClient) -> None:
    post_resp = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes(), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes(), "application/x-yaml"),
        },
    )
    job_id = post_resp.json()["job_id"]

    get_resp = client.get(f"/download/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.headers["content-type"] == "application/pdf"


def test_get_download_pdf_content_is_valid(client: TestClient) -> None:
    post_resp = client.post(
        "/annotate",
        files={
            "pdf_file": ("input.pdf", _make_pdf_bytes(), "application/pdf"),
            "rules_file": ("rules.yaml", _make_rules_bytes(), "application/x-yaml"),
        },
    )
    job_id = post_resp.json()["job_id"]

    get_resp = client.get(f"/download/{job_id}")
    # Valid PDFs start with %PDF
    assert get_resp.content[:4] == b"%PDF"


def test_get_download_unknown_job_returns_404(client: TestClient) -> None:
    get_resp = client.get("/download/nonexistent-job-id")
    assert get_resp.status_code == 404


# --- OpenAPI docs ---

def test_openapi_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
