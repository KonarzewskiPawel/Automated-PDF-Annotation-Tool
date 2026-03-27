"""Tests for the gp_percentage plugin."""
from __future__ import annotations

from src.pdf_annotation_tool.models import MarkType, PluginResult
from src.plugins.gp_percentage import compute


def test_compute_returns_plugin_result() -> None:
    result = compute("Total Revenue 1,250,000\nGross Profit 500,000", {})
    assert isinstance(result, PluginResult)


def test_compute_correct_percentage() -> None:
    text = "Total Revenue 1,250,000\nGross Profit 500,000"
    result = compute(text, {})
    assert result.text == "GP 40%"


def test_compute_rounds_percentage() -> None:
    # 333 / 1000 = 33.3% → rounds to 33%
    text = "Total Revenue 1,000\nGross Profit 333"
    result = compute(text, {})
    assert result.text == "GP 33%"


def test_compute_mark_type_is_badge() -> None:
    text = "Total Revenue 1,000\nGross Profit 400"
    result = compute(text, {})
    assert result.mark_type == MarkType.BADGE


def test_compute_color_is_green_when_values_found() -> None:
    text = "Total Revenue 1,000\nGross Profit 400"
    result = compute(text, {})
    r, g, b = result.color
    assert g > r and g > b  # green dominant


def test_compute_fallback_when_missing_revenue() -> None:
    result = compute("Gross Profit 500,000", {})
    assert result.text == "GP ?%"


def test_compute_fallback_when_missing_gross_profit() -> None:
    result = compute("Total Revenue 1,250,000", {})
    assert result.text == "GP ?%"


def test_compute_fallback_when_zero_revenue() -> None:
    result = compute("Total Revenue 0\nGross Profit 500,000", {})
    assert result.text == "GP ?%"


def test_compute_ignores_extra_text() -> None:
    text = (
        "Income Statement – FY 2025\n"
        "Total Revenue 1,250,000\n"
        "Cost of Goods Sold 750,000\n"
        "Gross Profit 500,000\n"
        "Operating Expenses 200,000\n"
    )
    result = compute(text, {})
    assert result.text == "GP 40%"


def test_compute_no_import_fitz() -> None:
    """Plugin must not import fitz (PyMuPDF) in any form."""
    import src.plugins.gp_percentage as mod

    source_file = mod.__file__
    assert source_file is not None
    import ast
    with open(source_file) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "fitz", "Plugin must not 'import fitz'"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "fitz", "Plugin must not 'from fitz import ...'"
