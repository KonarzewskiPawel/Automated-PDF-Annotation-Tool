"""Find text occurrences in a PDF document."""
from __future__ import annotations

import fitz

from src.pdf_annotation_tool.models import MatchMode


def find_text(
    doc: fitz.Document,
    search: str,
    match: MatchMode = MatchMode.ALL,
    match_page: int | None = None,
) -> list[tuple[int, fitz.Rect]]:
    """Return a list of (page_number, bounding_rect) for occurrences of search text.

    match=ALL   – every occurrence across all pages (default)
    match=FIRST – only the first occurrence found
    match=PAGE  – only occurrences on the 0-indexed page given by match_page
    """
    results: list[tuple[int, fitz.Rect]] = []
    for page_num, page in enumerate(doc):
        if match == MatchMode.PAGE and page_num != match_page:
            continue
        for rect in page.search_for(search):
            results.append((page_num, rect))
            if match == MatchMode.FIRST:
                return results
    return results
