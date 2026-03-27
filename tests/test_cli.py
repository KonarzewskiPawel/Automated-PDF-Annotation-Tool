"""Tests for CLI entry point."""
import subprocess
import sys
import textwrap
from pathlib import Path

import fitz
import pytest


def _make_pdf(tmp_path: Path, text: str) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    path = tmp_path / "input.pdf"
    doc.save(str(path))
    doc.close()
    return path


def _make_rules(tmp_path: Path, search: str) -> Path:
    content = textwrap.dedent(f"""\
        rules:
          - name: "Tick {search}"
            type: tick
            search: "{search}"
    """)
    path = tmp_path / "rules.yaml"
    path.write_text(content)
    return path


def test_cli_produces_output_file(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()


def test_cli_prints_summary(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Gross Profit")
    rules_path = _make_rules(tmp_path, "Gross Profit")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert result.returncode == 0, result.stderr
    assert "1" in result.stdout  # marks placed count


def test_cli_zero_marks_when_no_match(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    rules_path = _make_rules(tmp_path, "NonexistentText")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert result.returncode == 1
    assert "0" in result.stdout


def test_cli_exit_code_0_when_all_rules_pass(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert result.returncode == 0, result.stderr


def test_cli_exit_code_1_when_any_rule_fails(tmp_path: Path) -> None:
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
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(content)
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert result.returncode == 1


def test_cli_displays_verification_table(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Total Revenue")
    rules_path = _make_rules(tmp_path, "Total Revenue")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert "PASS" in result.stdout
    assert "Tick Total Revenue" in result.stdout


def test_cli_verification_table_shows_fail(tmp_path: Path) -> None:
    pdf_path = _make_pdf(tmp_path, "Hello World")
    rules_path = _make_rules(tmp_path, "NonexistentText")
    output_path = tmp_path / "output.pdf"

    result = subprocess.run(
        [sys.executable, "-m", "src.cli", str(pdf_path), str(rules_path), "-o", str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )

    assert "FAIL" in result.stdout
