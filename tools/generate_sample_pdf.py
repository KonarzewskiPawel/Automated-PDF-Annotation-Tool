"""Generate sample PDFs for development and testing.

Produces 3 PDFs in samples/ with different page sizes, fonts, and layouts,
each containing financial-style labels suitable for annotation rules.

Usage:
    python tools/generate_sample_pdf.py
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

# Financial data rows: (label, value)
INCOME_STATEMENT = [
    ("Total Revenue", "1,250,000"),
    ("Cost of Goods Sold", "750,000"),
    ("Gross Profit", "500,000"),
    ("Operating Expenses", "200,000"),
    ("Operating Income", "300,000"),
    ("Net Income", "240,000"),
]

BALANCE_SHEET = [
    ("Total Assets", "3,400,000"),
    ("Total Liabilities", "1,900,000"),
    ("Total Equity", "1,500,000"),
    ("Current Assets", "800,000"),
    ("Current Liabilities", "600,000"),
    ("Retained Earnings", "900,000"),
]

CASH_FLOW = [
    ("Operating Cash Flow", "350,000"),
    ("Investing Activities", "-120,000"),
    ("Financing Activities", "-80,000"),
    ("Gross Profit", "500,000"),
    ("Total Revenue", "1,250,000"),
    ("Net Cash Change", "150,000"),
]


def _add_title(page: fitz.Page, title: str, font: str, y: float) -> float:
    page.insert_text(
        (50, y),
        title,
        fontname=font,
        fontsize=16,
        color=(0, 0, 0),
    )
    return y + 30


def _add_table_rows(
    page: fitz.Page,
    rows: list[tuple[str, str]],
    font: str,
    start_y: float,
    label_x: float = 50,
    value_x: float = 300,
    row_height: float = 22,
) -> float:
    y = start_y
    for label, value in rows:
        page.insert_text((label_x, y), label, fontname=font, fontsize=11)
        page.insert_text((value_x, y), value, fontname=font, fontsize=11)
        y += row_height
    return y


def generate_income_statement(output_dir: Path) -> Path:
    """A4 portrait (595x842 pt) with Helvetica font, standard layout."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 60.0
    y = _add_title(page, "Income Statement – FY 2025", "helv", y)
    y += 10
    _add_table_rows(page, INCOME_STATEMENT, "helv", y)
    out = output_dir / "income_statement.pdf"
    doc.save(str(out))
    doc.close()
    return out


def generate_balance_sheet(output_dir: Path) -> Path:
    """Letter landscape (792x612 pt) with Courier font, two-column layout."""
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)
    y = 60.0
    y = _add_title(page, "Balance Sheet – FY 2025", "cour", y)
    y += 10
    _add_table_rows(page, BALANCE_SHEET, "cour", y, label_x=50, value_x=400)
    out = output_dir / "balance_sheet.pdf"
    doc.save(str(out))
    doc.close()
    return out


def generate_cash_flow(output_dir: Path) -> Path:
    """Legal size (612x1008 pt) with Times font, indented layout."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=1008)
    y = 80.0
    y = _add_title(page, "Cash Flow Statement – FY 2025", "tiro", y)
    y += 10
    _add_table_rows(page, CASH_FLOW, "tiro", y, label_x=70, value_x=320)
    out = output_dir / "cash_flow.pdf"
    doc.save(str(out))
    doc.close()
    return out


def generate_all(output_dir: Path | None = None) -> list[Path]:
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        generate_income_statement(output_dir),
        generate_balance_sheet(output_dir),
        generate_cash_flow(output_dir),
    ]


if __name__ == "__main__":
    paths = generate_all()
    for p in paths:
        print(f"Generated: {p}")
