"""Tests for text_finder module."""
from pathlib import Path

import fitz
import pytest

from src.pdf_annotation_tool.models import MatchMode
from src.pdf_annotation_tool.text_finder import find_text


def _make_pdf(tmp_path: Path, text: str) -> str:
    """Create a minimal PDF with given text and return its path."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    path = str(tmp_path / "test.pdf")
    doc.save(path)
    doc.close()
    return path


def test_find_existing_text(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    doc = fitz.open(pdf_path)
    results = find_text(doc, "Total Revenue")
    doc.close()
    assert len(results) > 0


def test_find_text_returns_page_and_rect(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Gross Profit")
    doc = fitz.open(pdf_path)
    results = find_text(doc, "Gross Profit")
    doc.close()
    assert len(results) == 1
    page_num, rect = results[0]
    assert page_num == 0
    assert rect.width > 0
    assert rect.height > 0


def test_find_missing_text_returns_empty(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    doc = fitz.open(pdf_path)
    results = find_text(doc, "NonexistentString")
    doc.close()
    assert results == []


def test_find_text_multiple_pages(tmp_path: Path) -> None:
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page()
        page.insert_text((50, 100), "Net Income", fontsize=12)
    path = str(tmp_path / "multi.pdf")
    doc.save(path)
    doc.close()

    doc = fitz.open(path)
    results = find_text(doc, "Net Income")
    doc.close()
    assert len(results) == 3
    assert {r[0] for r in results} == {0, 1, 2}


# --- Match mode tests ---

def test_find_text_match_first_returns_one_result(tmp_path: Path) -> None:
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page()
        page.insert_text((50, 100), "Revenue", fontsize=12)
    path = str(tmp_path / "multi.pdf")
    doc.save(path)
    doc.close()

    doc = fitz.open(path)
    results = find_text(doc, "Revenue", match=MatchMode.FIRST)
    doc.close()
    assert len(results) == 1
    assert results[0][0] == 0  # first page


def test_find_text_match_page_returns_only_that_page(tmp_path: Path) -> None:
    doc = fitz.open()
    for _ in range(3):
        page = doc.new_page()
        page.insert_text((50, 100), "Revenue", fontsize=12)
    path = str(tmp_path / "multi.pdf")
    doc.save(path)
    doc.close()

    doc = fitz.open(path)
    # match_page=1 means page index 1 (second page, 0-indexed)
    results = find_text(doc, "Revenue", match=MatchMode.PAGE, match_page=1)
    doc.close()
    assert len(results) == 1
    assert results[0][0] == 1


def test_find_text_match_page_no_match_returns_empty(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Revenue")
    doc = fitz.open(pdf_path)
    # match_page=5 doesn't exist in a 1-page doc
    results = find_text(doc, "Revenue", match=MatchMode.PAGE, match_page=5)
    doc.close()
    assert results == []


def test_find_text_match_all_is_default(tmp_path: Path) -> None:
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page()
        page.insert_text((50, 100), "Revenue", fontsize=12)
    path = str(tmp_path / "multi.pdf")
    doc.save(path)
    doc.close()

    doc = fitz.open(path)
    results = find_text(doc, "Revenue")
    doc.close()
    assert len(results) == 2
