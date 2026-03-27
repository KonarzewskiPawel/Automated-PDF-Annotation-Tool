"""Load annotation rules from a YAML file."""
from __future__ import annotations

from pathlib import Path

import yaml

from src.pdf_annotation_tool.mark_placer import SHADING_COLORS
from src.pdf_annotation_tool.models import MarkType, MatchMode, Position, Rule


def load_rules(rules_path: str) -> list[Rule]:
    """Parse a YAML rules file and return a list of Rule objects."""
    text = Path(rules_path).read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    rules: list[Rule] = []
    for item in data.get("rules", []):
        raw_type = item.get("type")

        match_str = str(item.get("match", "all"))
        if match_str.startswith("page:"):
            match_mode = MatchMode.PAGE
            match_page: int | None = int(match_str.split(":", 1)[1]) - 1  # 1-indexed → 0-indexed
        else:
            match_mode = MatchMode(match_str)
            match_page = None

        raw_fill_color = item.get("fill_color")
        if raw_fill_color is not None and raw_fill_color not in SHADING_COLORS:
            raise ValueError(
                f"Rule '{item.get('name', '?')}': invalid fill_color '{raw_fill_color}'. "
                f"Must be one of: {sorted(SHADING_COLORS)}"
            )

        raw_badge_text = item.get("badge_text")

        if raw_type == "shading_badge":
            if raw_fill_color is None:
                raise ValueError(
                    f"Rule '{item.get('name', '?')}': shading_badge rules require fill_color. "
                    f"Must be one of: {sorted(SHADING_COLORS)}"
                )
            if not raw_badge_text:
                raise ValueError(
                    f"Rule '{item.get('name', '?')}': shading_badge rules require badge_text."
                )

        rule = Rule(
            name=item["name"],
            search=item["search"],
            type=MarkType(raw_type) if raw_type else None,
            plugin=item.get("plugin"),
            position=Position(item.get("position", "right")),
            match=match_mode,
            match_page=match_page,
            offset_x=float(item.get("offset_x", 0.0)),
            offset_y=float(item.get("offset_y", 0.0)),
            fill_color=raw_fill_color,
            badge_text=raw_badge_text,
        )
        rules.append(rule)
    return rules
