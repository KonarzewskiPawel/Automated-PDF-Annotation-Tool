"""Integration tests: full pipeline on generated sample PDFs.

Each test generates a PDF programmatically, builds a rules file, runs
annotate_pdf(), and asserts that annotations were placed and verification passed.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import fitz

from src.pdf_annotation_tool.service import annotate_pdf
from tools.generate_sample_pdf import (
    generate_balance_sheet,
    generate_cash_flow,
    generate_income_statement,
)


# ---------------------------------------------------------------------------
# Income Statement
# ---------------------------------------------------------------------------

def test_integration_income_statement_tick_total_revenue(tmp_path: Path) -> None:
    """Full pipeline: tick Total Revenue in generated income_statement.pdf."""
    pdf_path = str(generate_income_statement(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Total Revenue"
            type: tick
            search: "Total Revenue"
            position: right
            match: all
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed >= 1
    assert result.verification is not None
    assert result.verification.passed is True
    assert result.verification.rule_results[0].status == "PASS"


def test_integration_income_statement_multiple_rules(tmp_path: Path) -> None:
    """Full pipeline: tick both Total Revenue and Gross Profit."""
    pdf_path = str(generate_income_statement(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Total Revenue"
            type: tick
            search: "Total Revenue"
          - name: "Tick Gross Profit"
            type: tick
            search: "Gross Profit"
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 2
    assert result.verification is not None
    assert result.verification.passed is True
    statuses = {r.rule_name: r.status for r in result.verification.rule_results}
    assert statuses["Tick Total Revenue"] == "PASS"
    assert statuses["Tick Gross Profit"] == "PASS"


def test_integration_income_statement_annotation_count(tmp_path: Path) -> None:
    """Verification total_annotations matches marks_placed for income_statement."""
    pdf_path = str(generate_income_statement(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Net Income"
            type: tick
            search: "Net Income"
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.total_annotations == result.marks_placed


# ---------------------------------------------------------------------------
# Balance Sheet
# ---------------------------------------------------------------------------

def test_integration_balance_sheet_tick_total_equity(tmp_path: Path) -> None:
    """Full pipeline: tick Total Equity in generated balance_sheet.pdf."""
    pdf_path = str(generate_balance_sheet(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Total Equity"
            type: tick
            search: "Total Equity"
            position: right
            match: all
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed >= 1
    assert result.verification is not None
    assert result.verification.passed is True
    assert result.verification.rule_results[0].status == "PASS"


def test_integration_balance_sheet_multiple_rules(tmp_path: Path) -> None:
    """Full pipeline: flag Total Assets and back_reference Total Liabilities."""
    pdf_path = str(generate_balance_sheet(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Flag Total Assets"
            type: flag
            search: "Total Assets"
          - name: "Ref Total Liabilities"
            type: back_reference
            search: "Total Liabilities"
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 2
    assert result.verification is not None
    assert result.verification.passed is True


def test_integration_balance_sheet_verification_fail_missing_text(tmp_path: Path) -> None:
    """Verification FAIL when rule targets text not present in balance_sheet.pdf."""
    pdf_path = str(generate_balance_sheet(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Total Equity"
            type: tick
            search: "Total Equity"
          - name: "Missing Rule"
            type: tick
            search: "NonexistentLabel"
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.verification is not None
    assert result.verification.passed is False
    statuses = {r.rule_name: r.status for r in result.verification.rule_results}
    assert statuses["Tick Total Equity"] == "PASS"
    assert statuses["Missing Rule"] == "FAIL"


# ---------------------------------------------------------------------------
# Cash Flow
# ---------------------------------------------------------------------------

def test_integration_cash_flow_tick_operating_cash_flow(tmp_path: Path) -> None:
    """Full pipeline: tick Operating Cash Flow in generated cash_flow.pdf."""
    pdf_path = str(generate_cash_flow(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Operating Cash Flow"
            type: tick
            search: "Operating Cash Flow"
            position: right
            match: all
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed >= 1
    assert result.verification is not None
    assert result.verification.passed is True
    assert result.verification.rule_results[0].status == "PASS"


def test_integration_cash_flow_all_mark_types(tmp_path: Path) -> None:
    """Full pipeline: use tick, flag, back_reference in cash_flow.pdf."""
    pdf_path = str(generate_cash_flow(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Operating Cash Flow"
            type: tick
            search: "Operating Cash Flow"
          - name: "Flag Total Revenue"
            type: flag
            search: "Total Revenue"
          - name: "Ref Gross Profit"
            type: back_reference
            search: "Gross Profit"
    """))
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 3
    assert result.verification is not None
    assert result.verification.passed is True


def test_integration_cash_flow_output_file_is_valid_pdf(tmp_path: Path) -> None:
    """Output from cash_flow pipeline is a valid PDF that can be reopened."""
    pdf_path = str(generate_cash_flow(tmp_path))
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(textwrap.dedent("""\
        rules:
          - name: "Tick Net Cash Change"
            type: tick
            search: "Net Cash Change"
    """))
    output_path = str(tmp_path / "output.pdf")

    annotate_pdf(pdf_path, rules_path, output_path)

    doc = fitz.open(output_path)
    assert doc.page_count >= 1
    total_annots = sum(len(list(doc[i].annots())) for i in range(doc.page_count))
    assert total_annots >= 1
    doc.close()
