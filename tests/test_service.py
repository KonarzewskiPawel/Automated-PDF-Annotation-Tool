"""Tests for service layer."""
import logging
import textwrap
from pathlib import Path

import fitz
import pytest

from src.pdf_annotation_tool.service import annotate_pdf


def _make_pdf(tmp_path: Path, text: str, pages: int = 1) -> str:
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((50, 100), text, fontsize=12)
    path = str(tmp_path / "input.pdf")
    doc.save(path)
    doc.close()
    return path


def _make_rules(tmp_path: Path, search: str, mark_type: str = "tick",
                position: str = "right", match: str = "all",
                offset_x: float = 0.0, offset_y: float = 0.0) -> str:
    lines = [
        "rules:",
        f'  - name: "Tick {search}"',
        f"    type: {mark_type}",
        f'    search: "{search}"',
        f"    position: {position}",
        f"    match: {match}",
    ]
    if offset_x != 0.0:
        lines.append(f"    offset_x: {offset_x}")
    if offset_y != 0.0:
        lines.append(f"    offset_y: {offset_y}")
    content = "\n".join(lines) + "\n"
    path = str(tmp_path / "rules.yaml")
    Path(path).write_text(content)
    return path


def test_annotate_pdf_returns_result(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.input_path == pdf_path
    assert result.output_path == output_path
    assert result.marks_placed == 1


def test_annotate_pdf_creates_output_file(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Gross Profit")
    rules_path = _make_rules(tmp_path, "Gross Profit")
    output_path = str(tmp_path / "output.pdf")

    annotate_pdf(pdf_path, rules_path, output_path)

    assert Path(output_path).exists()


def test_annotate_pdf_output_has_freetext_annotation(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Net Income")
    rules_path = _make_rules(tmp_path, "Net Income")
    output_path = str(tmp_path / "output.pdf")

    annotate_pdf(pdf_path, rules_path, output_path)

    doc = fitz.open(output_path)
    page = doc[0]
    annots = list(page.annots())
    assert len(annots) == 1
    assert annots[0].type[1] == "FreeText"
    doc.close()


def test_annotate_pdf_no_match_places_zero_marks(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    rules_path = _make_rules(tmp_path, "NonexistentText")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 0


def test_annotate_pdf_details_include_rule_name(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Equity")
    rules_path = _make_rules(tmp_path, "Total Equity")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert len(result.details) == 1
    assert result.details[0]["rule"] == "Tick Total Equity"
    assert result.details[0]["page"] == 0


# --- New mark types via service ---

def test_annotate_flag_places_mark(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Net Income")
    rules_path = _make_rules(tmp_path, "Net Income", mark_type="flag")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1
    doc = fitz.open(output_path)
    annot = list(doc[0].annots())[0]
    assert annot.info.get("content") == "⚑"
    doc.close()


def test_annotate_back_reference_places_mark(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue", mark_type="back_reference")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1
    doc = fitz.open(output_path)
    annot = list(doc[0].annots())[0]
    assert annot.info.get("content") == "←"
    doc.close()


def test_annotate_paragraph_end_flush_right(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Cash Flow.")
    rules_path = _make_rules(tmp_path, "Cash Flow.", mark_type="paragraph_end",
                             position="flush_right")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1
    doc = fitz.open(output_path)
    annot = list(doc[0].annots())[0]
    assert annot.info.get("content") == "/"
    doc.close()


# --- Match modes via service ---

def test_annotate_match_first_places_one_mark_across_pages(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Revenue", pages=3)
    rules_path = _make_rules(tmp_path, "Revenue", match="first")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1


def test_annotate_match_page_places_only_on_specified_page(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Revenue", pages=3)
    rules_path = _make_rules(tmp_path, "Revenue", match='"page:2"')
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1
    assert result.details[0]["page"] == 1  # 0-indexed page 1 = page 2 in YAML


def test_annotate_match_all_places_on_all_pages(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Revenue", pages=3)
    rules_path = _make_rules(tmp_path, "Revenue", match="all")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 3


# --- Verification block (issue-6) ---

def test_verification_pass_when_rule_matches(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.passed is True
    assert len(result.verification.rule_results) == 1
    assert result.verification.rule_results[0].status == "PASS"
    assert result.verification.rule_results[0].annotations_found >= 1


def test_verification_fail_when_rule_not_found(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    rules_path = _make_rules(tmp_path, "NonexistentText")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.passed is False
    assert result.verification.rule_results[0].status == "FAIL"
    assert result.verification.rule_results[0].annotations_found == 0


def test_verification_overall_fail_when_any_rule_fails(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    content = textwrap.dedent("""\
        rules:
          - name: "Tick Total Revenue"
            type: tick
            search: "Total Revenue"
          - name: "Tick Missing"
            type: tick
            search: "NonexistentText"
    """)
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(content)
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.passed is False
    statuses = {r.rule_name: r.status for r in result.verification.rule_results}
    assert statuses["Tick Total Revenue"] == "PASS"
    assert statuses["Tick Missing"] == "FAIL"


def test_verification_total_annotations_count(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.total_annotations == 1


# --- SHADING_BADGE via service ---

def test_annotate_shading_badge_places_mark(tmp_path: Path) -> None:
    """annotate_pdf places a SHADING_BADGE annotation through the full pipeline."""
    pdf_path = _make_pdf(tmp_path, "Operating Cash Flow")
    rules_content = textwrap.dedent("""\
        rules:
          - name: "Warn Cash Flow"
            type: shading_badge
            search: "Operating Cash Flow"
            fill_color: amber
            badge_text: "WARN"
    """)
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(rules_content)
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1
    doc = fitz.open(output_path)
    page = doc[0]  # keep page reference alive so annotations stay bound
    annots = list(page.annots())
    assert len(annots) == 1
    assert annots[0].type[1] == "FreeText"
    assert annots[0].info.get("content") == "WARN"
    doc.close()


def test_annotate_shading_badge_verification_passes(tmp_path: Path) -> None:
    """SHADING_BADGE match is counted in the verification result."""
    pdf_path = _make_pdf(tmp_path, "Net Income")
    rules_content = textwrap.dedent("""\
        rules:
          - name: "Error Marker"
            type: shading_badge
            search: "Net Income"
            fill_color: red
            badge_text: "ERR"
    """)
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(rules_content)
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.passed is True
    assert result.verification.rule_results[0].annotations_found == 1


def test_warning_logged_when_rule_not_found(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    rules_path = _make_rules(tmp_path, "NonexistentText")
    output_path = str(tmp_path / "output.pdf")

    with caplog.at_level(logging.WARNING, logger="src.pdf_annotation_tool.service"):
        annotate_pdf(pdf_path, rules_path, output_path)

    assert any("NonexistentText" in r.message for r in caplog.records)
