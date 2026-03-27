"""Gross Profit percentage computed badge plugin.

Extracts Total Revenue and Gross Profit values from page text and computes
the GP% (Gross Profit / Total Revenue * 100), returning a badge like "GP 40%".
"""
from __future__ import annotations

import re
from typing import Any

# Import PluginResult and MarkType via a local import to avoid fitz dependency
from src.pdf_annotation_tool.models import MarkType, PluginResult

# Compiled patterns for extracting labelled numeric values from page text
_GROSS_PROFIT_RE = re.compile(r"Gross Profit\s+([-]?[\d,]+(?:\.\d+)?)")
_TOTAL_REVENUE_RE = re.compile(r"Total Revenue\s+([-]?[\d,]+(?:\.\d+)?)")


def _extract_value(text: str, pattern: re.Pattern[str]) -> float | None:
    """Return the first number captured by pattern in text, or None."""
    match = pattern.search(text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def compute(text: str, config: dict[str, Any]) -> PluginResult:
    """Compute GP% from page text content.

    Args:
        text: Full text of the PDF page containing the matched annotation target.
        config: Rule config dict (unused by this plugin).

    Returns:
        PluginResult with badge text (e.g. "GP 40%"), color, and mark_type.
    """
    gross_profit = _extract_value(text, _GROSS_PROFIT_RE)
    total_revenue = _extract_value(text, _TOTAL_REVENUE_RE)

    if gross_profit is not None and total_revenue is not None and total_revenue != 0:
        pct = round(gross_profit / total_revenue * 100)
        return PluginResult(
            text=f"GP {pct}%",
            color=(0.0, 0.6, 0.0),
            mark_type=MarkType.BADGE,
        )

    return PluginResult(
        text="GP ?%",
        color=(0.8, 0.0, 0.0),
        mark_type=MarkType.BADGE,
    )
