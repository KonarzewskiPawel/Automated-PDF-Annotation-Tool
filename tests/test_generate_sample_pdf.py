"""Tests for tools/generate_sample_pdf.py"""
import importlib.util
from pathlib import Path

import fitz  # PyMuPDF
import pytest

TOOLS_DIR = Path(__file__).parent.parent / "tools"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_sample_pdf", TOOLS_DIR / "generate_sample_pdf.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_generates_three_pdfs(tmp_path):
    mod = _load_generator()
    mod.generate_all(output_dir=tmp_path)
    pdfs = sorted(tmp_path.glob("*.pdf"))
    assert len(pdfs) == 3, f"Expected 3 PDFs, got {len(pdfs)}"


def test_pdfs_have_different_page_sizes(tmp_path):
    mod = _load_generator()
    mod.generate_all(output_dir=tmp_path)
    pdfs = sorted(tmp_path.glob("*.pdf"))
    sizes = set()
    for pdf_path in pdfs:
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        sizes.add((round(page.rect.width), round(page.rect.height)))
        doc.close()
    assert len(sizes) == 3, f"Expected 3 distinct page sizes, got {sizes}"


def test_pdfs_contain_financial_labels(tmp_path):
    mod = _load_generator()
    mod.generate_all(output_dir=tmp_path)
    required_terms = {"Total Revenue", "Total Equity", "Gross Profit"}
    found: set[str] = set()
    for pdf_path in sorted(tmp_path.glob("*.pdf")):
        doc = fitz.open(str(pdf_path))
        for page in doc:
            text = page.get_text()
            for term in required_terms:
                if term in text:
                    found.add(term)
        doc.close()
    assert required_terms <= found, f"Missing financial labels: {required_terms - found}"


def test_pdfs_have_text_content(tmp_path):
    mod = _load_generator()
    mod.generate_all(output_dir=tmp_path)
    for pdf_path in sorted(tmp_path.glob("*.pdf")):
        doc = fitz.open(str(pdf_path))
        all_text = "".join(page.get_text() for page in doc)
        doc.close()
        assert len(all_text.strip()) > 50, f"{pdf_path.name} has too little text"
