"""FastAPI layer for the PDF annotation tool."""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.pdf_annotation_tool.service import annotate_pdf

app = FastAPI(
    title="PDF Annotation Tool",
    description="REST API for annotating PDFs with marks based on YAML rules.",
    version="0.1.0",
)

# In-memory store mapping job_id → annotated PDF path
_jobs: dict[str, str] = {}


class RuleVerificationResultSchema(BaseModel):
    rule_name: str
    status: str
    annotations_found: int


class VerificationResultSchema(BaseModel):
    passed: bool
    total_annotations: int
    rule_results: list[RuleVerificationResultSchema]


class AnnotateResponse(BaseModel):
    job_id: str
    marks_placed: int
    details: list[dict[str, object]]
    verification: VerificationResultSchema | None = None


@app.post("/annotate", response_model=AnnotateResponse)
async def annotate(
    pdf_file: UploadFile,
    rules_file: UploadFile,
) -> AnnotateResponse:
    """Accept a PDF and YAML rules file, annotate the PDF, and return results."""
    pdf_bytes = await pdf_file.read()
    rules_bytes = await rules_file.read()

    # Validate PDF magic bytes
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=422, detail="Uploaded PDF file is not a valid PDF.")

    # Validate YAML is parseable
    try:
        yaml.safe_load(rules_bytes.decode("utf-8"))
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid YAML rules file: {exc}") from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        input_pdf_path = str(tmp / "input.pdf")
        rules_path = str(tmp / "rules.yaml")
        output_pdf_path = str(tmp / "output.pdf")

        Path(input_pdf_path).write_bytes(pdf_bytes)
        Path(rules_path).write_bytes(rules_bytes)

        try:
            result = annotate_pdf(input_pdf_path, rules_path, output_pdf_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Annotation failed: {exc}") from exc

        # Move annotated PDF to a persistent temp file for download
        job_id = str(uuid.uuid4())
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix=f"annotated_{job_id}_"
        ) as f:
            f.write(Path(output_pdf_path).read_bytes())
            persistent_path = f.name
        _jobs[job_id] = persistent_path

    verification = None
    if result.verification is not None:
        v = result.verification
        verification = VerificationResultSchema(
            passed=v.passed,
            total_annotations=v.total_annotations,
            rule_results=[
                RuleVerificationResultSchema(
                    rule_name=r.rule_name,
                    status=r.status,
                    annotations_found=r.annotations_found,
                )
                for r in v.rule_results
            ],
        )

    return AnnotateResponse(
        job_id=job_id,
        marks_placed=result.marks_placed,
        details=result.details,
        verification=verification,
    )


@app.get("/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    """Download the annotated PDF for a given job ID."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    path = _jobs[job_id]
    if not Path(path).exists():
        raise HTTPException(status_code=404, detail=f"Annotated PDF for job '{job_id}' no longer available.")
    return FileResponse(path, media_type="application/pdf", filename="annotated.pdf")
