"""CLI entry point for the PDF annotation tool.

Usage:
    python -m src.cli <input_pdf> <rules_yaml> -o <output_pdf>
"""
from __future__ import annotations

import argparse
import sys

from src.pdf_annotation_tool.service import annotate_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Annotate a PDF according to a YAML rules file."
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("rules_yaml", help="Path to the YAML rules file")
    parser.add_argument("-o", "--output", required=True, help="Path for the annotated output PDF")
    args = parser.parse_args(argv)

    result = annotate_pdf(args.input_pdf, args.rules_yaml, args.output)

    print(f"Annotated PDF saved to: {result.output_path}")
    print(f"Marks placed: {result.marks_placed}")
    for detail in result.details:
        print(f"  - [{detail['rule']}] page {detail['page']}")

    if result.verification is not None:
        v = result.verification
        print()
        print("Verification results:")
        print(f"  {'Rule':<40} {'Status':<6} {'Annotations'}")
        print(f"  {'-' * 40} {'-' * 6} {'-' * 11}")
        for r in v.rule_results:
            print(f"  {r.rule_name:<40} {r.status:<6} {r.annotations_found}")
        print()
        overall = "PASS" if v.passed else "FAIL"
        print(f"Overall: {overall} ({v.total_annotations} total annotations)")

        return 0 if v.passed else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
