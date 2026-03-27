"""Demonstration test: insert_text() silently drops Unicode symbols.

This test documents WHY all marks are placed via add_freetext_annot() rather
than insert_text().  The Helvetica built-in font has no glyph for the tick
mark (U+2713 ✓), so PyMuPDF substitutes a replacement character instead of
rendering the intended symbol.  Freetext annotations, by contrast, embed the
character correctly as annotation content.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest


@pytest.fixture
def blank_pdf(tmp_path: Path) -> Path:
    """Return the path to a one-page blank PDF."""
    doc = fitz.open()
    doc.new_page()
    path = tmp_path / "blank.pdf"
    doc.save(str(path))
    doc.close()
    return path


class TestInsertTextUnicodeFailure:
    """insert_text() silently replaces ✓ with a substitute glyph."""

    def test_insert_text_does_not_preserve_tick_in_content_stream(
        self, blank_pdf: Path, tmp_path: Path
    ) -> None:
        """insert_text() claims to write 1 char but stores a replacement glyph."""
        out = tmp_path / "out.pdf"
        doc = fitz.open(str(blank_pdf))
        page = doc[0]

        # insert_text() returns the number of characters "written"
        chars_written = page.insert_text((100, 100), "✓", fontname="helv", fontsize=12)
        assert chars_written == 1, "PyMuPDF claims to write 1 character"

        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        page2 = doc2[0]
        content_text = page2.get_text()
        doc2.close()

        # The content stream does NOT contain the tick — a replacement glyph is
        # stored instead (commonly rendered as '·').
        assert "✓" not in content_text, (
            "insert_text() should NOT preserve ✓ in the content stream "
            f"(got: {content_text!r})"
        )

    def test_insert_text_tick_not_findable_via_search(
        self, blank_pdf: Path, tmp_path: Path
    ) -> None:
        """page.search_for('✓') returns no hits after insert_text()."""
        out = tmp_path / "out.pdf"
        doc = fitz.open(str(blank_pdf))
        page = doc[0]
        page.insert_text((100, 100), "✓", fontname="helv", fontsize=12)
        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        hits = doc2[0].search_for("✓")
        doc2.close()

        assert hits == [], (
            "insert_text() result should not be findable via search_for('✓')"
        )

    def test_freetext_annot_correctly_stores_tick(
        self, blank_pdf: Path, tmp_path: Path
    ) -> None:
        """add_freetext_annot() correctly creates an annotation containing ✓."""
        out = tmp_path / "out.pdf"
        doc = fitz.open(str(blank_pdf))
        page = doc[0]

        annot_rect = fitz.Rect(100, 90, 120, 104)
        page.add_freetext_annot(
            annot_rect,
            "✓",
            fontsize=10,
            fontname="helv",
            text_color=(0, 0.6, 0),
            fill_color=(1, 1, 1),
        )

        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        annots = list(doc2[0].annots())
        doc2.close()

        assert len(annots) == 1, "Exactly one freetext annotation should be present"

    def test_freetext_annot_content_matches_tick(
        self, blank_pdf: Path, tmp_path: Path
    ) -> None:
        """The freetext annotation's content field holds the exact ✓ character."""
        out = tmp_path / "out.pdf"
        doc = fitz.open(str(blank_pdf))
        page = doc[0]

        page.add_freetext_annot(
            fitz.Rect(100, 90, 120, 104),
            "✓",
            fontsize=10,
            fontname="helv",
            text_color=(0, 0.6, 0),
            fill_color=(1, 1, 1),
        )

        doc.save(str(out))
        doc.close()

        doc2 = fitz.open(str(out))
        annot = next(doc2[0].annots())
        content = annot.info["content"]
        doc2.close()

        assert content == "✓", (
            f"Freetext annotation content should be '✓', got {content!r}"
        )
