"""Tests for mark_placer module."""
import fitz
import pytest

from src.pdf_annotation_tool.mark_placer import place_mark, place_tick
from src.pdf_annotation_tool.models import MarkType, Position


def _make_doc_with_text(text: str) -> tuple[fitz.Document, fitz.Rect]:
    """Return an in-memory doc and the bounding rect of the inserted text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    rects = page.search_for(text)
    assert rects, f"Text '{text}' not found after insertion"
    return doc, rects[0]


def test_place_tick_creates_annotation() -> None:
    doc, text_rect = _make_doc_with_text("Total Revenue")
    page = doc[0]
    place_tick(page, text_rect)
    annots = list(page.annots())
    assert len(annots) == 1


def test_place_tick_is_freetext() -> None:
    doc, text_rect = _make_doc_with_text("Gross Profit")
    page = doc[0]
    place_tick(page, text_rect)
    annot = list(page.annots())[0]
    assert annot.type[1] == "FreeText"


def test_place_tick_contains_check_mark() -> None:
    doc, text_rect = _make_doc_with_text("Net Income")
    page = doc[0]
    place_tick(page, text_rect)
    annot = list(page.annots())[0]
    assert annot.info.get("content") == "✓"


def test_place_tick_positioned_to_right_of_text() -> None:
    doc, text_rect = _make_doc_with_text("Total Equity")
    page = doc[0]
    place_tick(page, text_rect)
    annot = list(page.annots())[0]
    # The annotation rect should start at or after the right edge of the text
    assert annot.rect.x0 >= text_rect.x1


# --- place_mark: new mark types ---

def test_place_mark_flag_contains_flag_symbol() -> None:
    doc, text_rect = _make_doc_with_text("Net Income")
    page = doc[0]
    place_mark(page, text_rect, MarkType.FLAG, Position.RIGHT)
    annot = list(page.annots())[0]
    assert annot.info.get("content") == "⚑"


def test_place_mark_back_reference_contains_arrow() -> None:
    doc, text_rect = _make_doc_with_text("Total Revenue")
    page = doc[0]
    place_mark(page, text_rect, MarkType.BACK_REFERENCE, Position.RIGHT)
    annot = list(page.annots())[0]
    assert annot.info.get("content") == "←"


def test_place_mark_paragraph_end_contains_slash() -> None:
    doc, text_rect = _make_doc_with_text("Cash Flow.")
    page = doc[0]
    place_mark(page, text_rect, MarkType.PARAGRAPH_END, Position.FLUSH_RIGHT)
    annot = list(page.annots())[0]
    assert annot.info.get("content") == "/"


# --- place_mark: position modes ---

def test_place_mark_position_left() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]
    place_mark(page, text_rect, MarkType.TICK, Position.LEFT)
    annot = list(page.annots())[0]
    assert annot.rect.x1 <= text_rect.x0


def test_place_mark_position_above() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]
    place_mark(page, text_rect, MarkType.TICK, Position.ABOVE)
    annot = list(page.annots())[0]
    assert annot.rect.y1 <= text_rect.y0


def test_place_mark_position_below() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]
    place_mark(page, text_rect, MarkType.TICK, Position.BELOW)
    annot = list(page.annots())[0]
    assert annot.rect.y0 >= text_rect.y1


def test_place_mark_position_flush_right() -> None:
    doc, text_rect = _make_doc_with_text("Cash Flow.")
    page = doc[0]
    place_mark(page, text_rect, MarkType.PARAGRAPH_END, Position.FLUSH_RIGHT)
    annot = list(page.annots())[0]
    # Flush right: annotation starts exactly at x1 of text (no gap)
    assert annot.rect.x0 == text_rect.x1


def test_place_mark_position_right() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]
    place_mark(page, text_rect, MarkType.TICK, Position.RIGHT)
    annot = list(page.annots())[0]
    assert annot.rect.x0 >= text_rect.x1


# --- place_mark: offsets ---

def test_place_mark_offset_x_shifts_right() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]

    place_mark(page, text_rect, MarkType.TICK, Position.RIGHT, offset_x=0.0)
    base_x = list(page.annots())[0].rect.x0
    # Clear annots by recreating doc
    doc2, text_rect2 = _make_doc_with_text("Revenue")
    page2 = doc2[0]
    place_mark(page2, text_rect2, MarkType.TICK, Position.RIGHT, offset_x=10.0)
    shifted_x = list(page2.annots())[0].rect.x0
    assert shifted_x == pytest.approx(base_x + 10.0)


def test_place_mark_offset_y_shifts_down() -> None:
    doc, text_rect = _make_doc_with_text("Revenue")
    page = doc[0]

    place_mark(page, text_rect, MarkType.TICK, Position.RIGHT, offset_y=0.0)
    base_y = list(page.annots())[0].rect.y0
    doc2, text_rect2 = _make_doc_with_text("Revenue")
    page2 = doc2[0]
    place_mark(page2, text_rect2, MarkType.TICK, Position.RIGHT, offset_y=5.0)
    shifted_y = list(page2.annots())[0].rect.y0
    assert shifted_y == pytest.approx(base_y + 5.0)
