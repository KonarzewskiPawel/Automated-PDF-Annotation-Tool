"""Tests for plugin rules: rule_loader, mark_placer.place_badge, and service integration."""
from __future__ import annotations

import textwrap
from pathlib import Path

import fitz
import pytest

from src.pdf_annotation_tool.mark_placer import place_badge
from src.pdf_annotation_tool.models import MarkType, PluginResult
from src.pdf_annotation_tool.rule_loader import load_rules
from src.pdf_annotation_tool.service import annotate_pdf


# ---------------------------------------------------------------------------
# rule_loader: plugin field
# ---------------------------------------------------------------------------

def test_load_rule_with_plugin_field(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "GP Badge"
            search: "Gross Profit"
            plugin: gp_percentage
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))

    assert len(rules) == 1
    rule = rules[0]
    assert rule.plugin == "gp_percentage"
    assert rule.type is None


def test_tick_rule_plugin_is_none(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Tick Revenue"
            type: tick
            search: "Total Revenue"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].plugin is None
    assert rules[0].type == MarkType.TICK


# ---------------------------------------------------------------------------
# mark_placer: place_badge
# ---------------------------------------------------------------------------

def test_place_badge_creates_freetext_annotation() -> None:
    doc = fitz.open()
    page = doc.new_page()
    text_rect = fitz.Rect(50, 100, 150, 114)

    annot = place_badge(page, text_rect, "GP 40%", (0.0, 0.6, 0.0))

    assert annot is not None
    assert annot.type[1] == "FreeText"
    doc.close()


def test_place_badge_positioned_right_of_text() -> None:
    doc = fitz.open()
    page = doc.new_page()
    text_rect = fitz.Rect(50, 100, 150, 114)

    annot = place_badge(page, text_rect, "GP 40%", (0.0, 0.6, 0.0))

    badge_rect = annot.rect
    assert badge_rect.x0 > text_rect.x1
    doc.close()


def test_place_badge_text_content() -> None:
    doc = fitz.open()
    page = doc.new_page()
    text_rect = fitz.Rect(50, 100, 150, 114)

    annot = place_badge(page, text_rect, "GP 40%", (0.0, 0.6, 0.0))

    assert annot.info.get("content") == "GP 40%"
    doc.close()


# ---------------------------------------------------------------------------
# service: plugin rule integration
# ---------------------------------------------------------------------------

def _make_income_pdf(tmp_path: Path) -> str:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 80), "Income Statement – FY 2025", fontsize=14)
    page.insert_text((50, 110), "Total Revenue", fontsize=11)
    page.insert_text((200, 110), "1,250,000", fontsize=11)
    page.insert_text((50, 132), "Cost of Goods Sold", fontsize=11)
    page.insert_text((200, 132), "750,000", fontsize=11)
    page.insert_text((50, 154), "Gross Profit", fontsize=11)
    page.insert_text((200, 154), "500,000", fontsize=11)
    path = str(tmp_path / "income.pdf")
    doc.save(path)
    doc.close()
    return path


def _make_plugin_rules(tmp_path: Path) -> str:
    content = textwrap.dedent("""\
        rules:
          - name: "GP Badge"
            search: "Gross Profit"
            plugin: gp_percentage
    """)
    path = str(tmp_path / "rules.yaml")
    Path(path).write_text(content)
    return path


def test_service_plugin_rule_places_badge(tmp_path: Path) -> None:
    pdf_path = _make_income_pdf(tmp_path)
    rules_path = _make_plugin_rules(tmp_path)
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 1


def test_service_plugin_rule_badge_text_in_output(tmp_path: Path) -> None:
    pdf_path = _make_income_pdf(tmp_path)
    rules_path = _make_plugin_rules(tmp_path)
    output_path = str(tmp_path / "output.pdf")

    annotate_pdf(pdf_path, rules_path, output_path)

    doc = fitz.open(output_path)
    page = doc[0]
    annots = list(page.annots())
    assert len(annots) == 1
    assert annots[0].info.get("content") == "GP 40%"
    doc.close()


def test_service_unknown_plugin_skips_gracefully(tmp_path: Path) -> None:
    pdf_path = _make_income_pdf(tmp_path)
    content = textwrap.dedent("""\
        rules:
          - name: "Unknown Plugin"
            search: "Gross Profit"
            plugin: nonexistent_plugin
    """)
    rules_path = str(tmp_path / "rules.yaml")
    Path(rules_path).write_text(content)
    output_path = str(tmp_path / "output.pdf")

    result = annotate_pdf(pdf_path, rules_path, output_path)

    assert result.marks_placed == 0
