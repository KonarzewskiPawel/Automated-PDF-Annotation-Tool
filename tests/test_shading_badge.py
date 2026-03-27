"""Tests for the shading badge mark type.

Shading badges are freetext annotations with a coloured background (amber,
red, or yellow) used as status indicators.  They differ from plain badges in
that the fill colour is the prominent visual element rather than the text colour.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import fitz
import pytest

from src.pdf_annotation_tool.mark_placer import place_shading_badge
from src.pdf_annotation_tool.models import MarkType, Position
from src.pdf_annotation_tool.rule_loader import load_rules

# Shading colours defined by the PRD
AMBER = (1.0, 0.75, 0.0)
RED = (0.9, 0.2, 0.2)
YELLOW = (1.0, 0.95, 0.0)


def _make_doc_with_text(text: str) -> tuple[fitz.Document, fitz.Rect]:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    rects = page.search_for(text)
    assert rects
    return doc, rects[0]


class TestPlaceShadingBadge:
    """place_shading_badge() places a coloured-background freetext annotation."""

    def test_creates_freetext_annotation(self) -> None:
        doc, text_rect = _make_doc_with_text("Operating Cash Flow")
        page = doc[0]
        place_shading_badge(page, text_rect, "OK", AMBER)
        assert len(list(page.annots())) == 1

    def test_annotation_type_is_freetext(self) -> None:
        doc, text_rect = _make_doc_with_text("Total Revenue")
        page = doc[0]
        place_shading_badge(page, text_rect, "PASS", AMBER)
        annot = next(page.annots())
        assert annot.type[1] == "FreeText"

    def test_badge_text_in_annotation_content(self) -> None:
        doc, text_rect = _make_doc_with_text("Total Revenue")
        page = doc[0]
        place_shading_badge(page, text_rect, "WARN", RED)
        annot = next(page.annots())
        assert annot.info["content"] == "WARN"

    def test_amber_fill_color_stored(self, tmp_path: Path) -> None:
        """Amber fill_color is persisted and readable after save/reopen."""
        doc, text_rect = _make_doc_with_text("Gross Profit")
        page = doc[0]
        place_shading_badge(page, text_rect, "GP", AMBER)
        out = tmp_path / "out.pdf"
        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        annot = next(doc2[0].annots())
        # PyMuPDF exposes fill_color via colors['stroke'] for FreeText annotations
        stroke = annot.colors.get("stroke", [])
        doc2.close()
        assert list(stroke) == pytest.approx(list(AMBER), abs=0.01)

    def test_red_fill_color_stored(self, tmp_path: Path) -> None:
        doc, text_rect = _make_doc_with_text("Net Income")
        page = doc[0]
        place_shading_badge(page, text_rect, "ERR", RED)
        out = tmp_path / "out.pdf"
        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        annot = next(doc2[0].annots())
        stroke = annot.colors.get("stroke", [])
        doc2.close()
        assert list(stroke) == pytest.approx(list(RED), abs=0.01)

    def test_yellow_fill_color_stored(self, tmp_path: Path) -> None:
        doc, text_rect = _make_doc_with_text("Net Income")
        page = doc[0]
        place_shading_badge(page, text_rect, "NOTE", YELLOW)
        out = tmp_path / "out.pdf"
        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        annot = next(doc2[0].annots())
        stroke = annot.colors.get("stroke", [])
        doc2.close()
        assert list(stroke) == pytest.approx(list(YELLOW), abs=0.01)

    def test_annotation_placed_to_right_of_text(self) -> None:
        doc, text_rect = _make_doc_with_text("Total Revenue")
        page = doc[0]
        place_shading_badge(page, text_rect, "OK", AMBER, position=Position.RIGHT)
        annot = next(page.annots())
        assert annot.rect.x0 >= text_rect.x1

    def test_offset_shifts_annotation(self) -> None:
        doc, text_rect = _make_doc_with_text("Total Revenue")
        page = doc[0]
        place_shading_badge(page, text_rect, "OK", AMBER, offset_x=10.0)
        x_shifted = next(page.annots()).rect.x0

        doc2, text_rect2 = _make_doc_with_text("Total Revenue")
        page2 = doc2[0]
        place_shading_badge(page2, text_rect2, "OK", AMBER, offset_x=0.0)
        x_base = next(page2.annots()).rect.x0

        assert x_shifted == pytest.approx(x_base + 10.0)


class TestShadingBadgeMarkType:
    """MarkType.SHADING_BADGE is a recognised enum member."""

    def test_shading_badge_in_mark_type_enum(self) -> None:
        assert MarkType.SHADING_BADGE.value == "shading_badge"


class TestRuleLoaderShadingBadge:
    """rule_loader parses shading_badge rules including fill_color and badge_text."""

    def test_loads_shading_badge_rule(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "Warn Cash Flow"
                type: shading_badge
                search: "Operating Cash Flow"
                fill_color: amber
                badge_text: "WARN"
                position: right
                match: all
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        rules = load_rules(str(rules_file))

        assert len(rules) == 1
        rule = rules[0]
        assert rule.type == MarkType.SHADING_BADGE
        assert rule.fill_color == "amber"
        assert rule.badge_text == "WARN"

    def test_loads_red_shading_badge(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "Error Marker"
                type: shading_badge
                search: "Net Loss"
                fill_color: red
                badge_text: "ERR"
                match: first
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        rules = load_rules(str(rules_file))

        rule = rules[0]
        assert rule.type == MarkType.SHADING_BADGE
        assert rule.fill_color == "red"

    def test_invalid_fill_color_raises(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "Bad Color"
                type: shading_badge
                search: "Revenue"
                fill_color: purple
                badge_text: "X"
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        with pytest.raises(ValueError, match="fill_color"):
            load_rules(str(rules_file))

    def test_missing_fill_color_raises(self, tmp_path: Path) -> None:
        """shading_badge without fill_color should raise at load time."""
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "No Color"
                type: shading_badge
                search: "Revenue"
                badge_text: "WARN"
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        with pytest.raises(ValueError, match="fill_color"):
            load_rules(str(rules_file))

    def test_missing_badge_text_raises(self, tmp_path: Path) -> None:
        """shading_badge without badge_text should raise at load time."""
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "No Text"
                type: shading_badge
                search: "Revenue"
                fill_color: amber
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        with pytest.raises(ValueError, match="badge_text"):
            load_rules(str(rules_file))

    def test_empty_badge_text_raises(self, tmp_path: Path) -> None:
        """shading_badge with an empty badge_text should raise at load time."""
        yaml_content = textwrap.dedent("""\
            rules:
              - name: "Empty Text"
                type: shading_badge
                search: "Revenue"
                fill_color: amber
                badge_text: ""
        """)
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml_content)
        with pytest.raises(ValueError, match="badge_text"):
            load_rules(str(rules_file))
