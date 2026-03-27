"""Place annotation marks on PDF pages."""
from __future__ import annotations

import fitz

from src.pdf_annotation_tool.models import MarkType, Position

_GAP = 4.0     # gap between text edge and mark (for non-flush positions)
_WIDTH = 16.0  # annotation rect width
_HEIGHT = 14.0  # annotation rect height
# Approximate width per character for badge sizing
_BADGE_CHAR_WIDTH = 7.0

# Shading badge fill colours (background)
SHADING_COLORS: dict[str, tuple[float, float, float]] = {
    "amber": (1.0, 0.75, 0.0),
    "red":   (0.9, 0.2,  0.2),
    "yellow": (1.0, 0.95, 0.0),
}

_MARK_SYMBOL: dict[MarkType, str] = {
    MarkType.TICK: "✓",
    MarkType.FLAG: "⚑",
    MarkType.BACK_REFERENCE: "←",
    MarkType.PARAGRAPH_END: "/",
}

_MARK_COLOR: dict[MarkType, tuple[float, float, float]] = {
    MarkType.TICK: (0, 0.6, 0),           # green
    MarkType.FLAG: (0.8, 0, 0),            # red
    MarkType.BACK_REFERENCE: (0, 0, 0.8), # blue
    MarkType.PARAGRAPH_END: (0, 0.6, 0),  # green
}


def _compute_origin(
    text_rect: fitz.Rect,
    position: Position,
    width: float,
    height: float,
) -> tuple[float, float]:
    """Return the (x0, y0) origin for an annotation rect given a position."""
    if position == Position.RIGHT:
        return text_rect.x1 + _GAP, text_rect.y0
    elif position == Position.LEFT:
        return text_rect.x0 - width - _GAP, text_rect.y0
    elif position == Position.ABOVE:
        return text_rect.x0, text_rect.y0 - height - _GAP
    elif position == Position.BELOW:
        return text_rect.x0, text_rect.y1 + _GAP
    elif position == Position.FLUSH_RIGHT:
        return text_rect.x1, text_rect.y0  # no gap — flush against text
    else:
        return text_rect.x1 + _GAP, text_rect.y0


def place_mark(
    page: fitz.Page,
    text_rect: fitz.Rect,
    mark_type: MarkType,
    position: Position,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> fitz.Annot:
    """Place a freetext annotation mark on the page relative to text_rect.

    Positions:
      RIGHT       – to the right of the text, with a small gap
      LEFT        – to the left of the text, with a small gap
      ABOVE       – above the text, with a small gap
      BELOW       – below the text, with a small gap
      FLUSH_RIGHT – immediately at the right edge of the text (no gap)

    offset_x / offset_y shift the computed position in PDF units.
    """
    x0, y0 = _compute_origin(text_rect, position, _WIDTH, _HEIGHT)
    x0 += offset_x
    y0 += offset_y
    annot_rect = fitz.Rect(x0, y0, x0 + _WIDTH, y0 + _HEIGHT)

    return page.add_freetext_annot(
        annot_rect,
        _MARK_SYMBOL[mark_type],
        fontsize=10,
        fontname="helv",
        text_color=_MARK_COLOR[mark_type],
        fill_color=(1, 1, 1),
    )


def place_badge(
    page: fitz.Page,
    text_rect: fitz.Rect,
    badge_text: str,
    color: tuple[float, float, float],
    position: Position = Position.RIGHT,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> fitz.Annot:
    """Place a text badge annotation on the page relative to text_rect."""
    badge_width = len(badge_text) * _BADGE_CHAR_WIDTH
    x0, y0 = _compute_origin(text_rect, position, badge_width, _HEIGHT)
    x0 += offset_x
    y0 += offset_y
    annot_rect = fitz.Rect(x0, y0, x0 + badge_width, y0 + _HEIGHT)

    return page.add_freetext_annot(
        annot_rect,
        badge_text,
        fontsize=10,
        fontname="helv",
        text_color=color,
        fill_color=(1, 1, 1),
    )


def place_shading_badge(
    page: fitz.Page,
    text_rect: fitz.Rect,
    badge_text: str,
    fill_color: tuple[float, float, float],
    position: Position = Position.RIGHT,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> fitz.Annot:
    """Place a shading badge — a coloured-background freetext annotation.

    Unlike plain badges (white background, coloured text), shading badges use
    *fill_color* as a prominent background colour (amber, red, or yellow) with
    black text, making them suitable as status indicators.
    """
    badge_width = len(badge_text) * _BADGE_CHAR_WIDTH
    x0, y0 = _compute_origin(text_rect, position, badge_width, _HEIGHT)
    x0 += offset_x
    y0 += offset_y
    annot_rect = fitz.Rect(x0, y0, x0 + badge_width, y0 + _HEIGHT)

    return page.add_freetext_annot(
        annot_rect,
        badge_text,
        fontsize=10,
        fontname="helv",
        text_color=(0.0, 0.0, 0.0),  # black text on coloured background
        fill_color=fill_color,
    )


def place_tick(page: fitz.Page, text_rect: fitz.Rect) -> fitz.Annot:
    """Place a green tick mark (✓) to the right of text_rect."""
    return place_mark(page, text_rect, MarkType.TICK, Position.RIGHT)
