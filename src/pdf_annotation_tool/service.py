"""Service layer for PDF annotation."""
from __future__ import annotations

import logging
import shutil

import fitz

from src.pdf_annotation_tool.mark_placer import SHADING_COLORS, place_badge, place_mark, place_shading_badge
from src.pdf_annotation_tool.models import (
    AnnotationResult,
    MarkType,
    RuleVerificationResult,
    VerificationResult,
)
from src.pdf_annotation_tool.plugin_registry import get_plugin
from src.pdf_annotation_tool.rule_loader import load_rules
from src.pdf_annotation_tool.text_finder import find_text

logger = logging.getLogger(__name__)


def _verify_annotations(output_path: str, rule_counts: dict[str, int]) -> VerificationResult:
    """Reopen the saved PDF and verify per-rule annotation counts."""
    doc: fitz.Document = fitz.open(output_path)
    try:
        total_annotations = sum(len(list(page.annots())) for page in doc)
    finally:
        doc.close()

    rule_results: list[RuleVerificationResult] = []
    for rule_name, count in rule_counts.items():
        status = "PASS" if count >= 1 else "FAIL"
        rule_results.append(RuleVerificationResult(
            rule_name=rule_name,
            status=status,
            annotations_found=count,
        ))

    passed = all(r.status == "PASS" for r in rule_results)
    return VerificationResult(
        rule_results=rule_results,
        passed=passed,
        total_annotations=total_annotations,
    )


def annotate_pdf(input_path: str, rules_path: str, output_path: str) -> AnnotationResult:
    """Annotate a PDF according to rules and save to output_path.

    Uses incremental save to preserve the original PDF structure.
    Returns an AnnotationResult summarising what was placed, including verification.
    """
    # Copy source to destination so incremental save writes to the same file
    shutil.copy2(input_path, output_path)

    rules = load_rules(rules_path)
    doc: fitz.Document = fitz.open(output_path)

    marks_placed = 0
    details: list[dict[str, object]] = []
    rule_counts: dict[str, int] = {rule.name: 0 for rule in rules}

    try:
        for rule in rules:
            occurrences = find_text(
                doc, rule.search, match=rule.match, match_page=rule.match_page
            )
            if not occurrences:
                logger.warning(
                    "Rule '%s': search text '%s' not found in PDF",
                    rule.name,
                    rule.search,
                )
            if rule.plugin:
                compute = get_plugin(rule.plugin)
                if compute is None:
                    continue
                for page_num, rect in occurrences:
                    page = doc[page_num]
                    page_text = page.get_text()
                    plugin_result = compute(page_text, {})
                    place_badge(
                        page, rect, plugin_result.text, plugin_result.color,
                        position=rule.position,
                        offset_x=rule.offset_x, offset_y=rule.offset_y,
                    )
                    marks_placed += 1
                    rule_counts[rule.name] += 1
                    details.append({"rule": rule.name, "page": page_num, "rect": list(rect)})
            elif rule.type == MarkType.SHADING_BADGE:
                # rule_loader guarantees fill_color and badge_text are set for SHADING_BADGE
                if rule.fill_color is None or rule.badge_text is None:
                    raise ValueError(
                        f"Rule '{rule.name}': shading_badge requires fill_color and badge_text."
                    )
                fill_color = SHADING_COLORS[rule.fill_color]
                text = rule.badge_text
                for page_num, rect in occurrences:
                    page = doc[page_num]
                    place_shading_badge(
                        page, rect, text, fill_color,
                        position=rule.position,
                        offset_x=rule.offset_x, offset_y=rule.offset_y,
                    )
                    marks_placed += 1
                    rule_counts[rule.name] += 1
                    details.append({"rule": rule.name, "page": page_num, "rect": list(rect)})
            elif rule.type is not None:
                for page_num, rect in occurrences:
                    page = doc[page_num]
                    place_mark(page, rect, rule.type, rule.position,
                               offset_x=rule.offset_x, offset_y=rule.offset_y)
                    marks_placed += 1
                    rule_counts[rule.name] += 1
                    details.append({"rule": rule.name, "page": page_num, "rect": list(rect)})

        doc.save(output_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    finally:
        doc.close()

    verification = _verify_annotations(output_path, rule_counts)

    return AnnotationResult(
        input_path=input_path,
        output_path=output_path,
        marks_placed=marks_placed,
        details=details,
        verification=verification,
    )
