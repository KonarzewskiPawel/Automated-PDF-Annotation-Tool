"""Tests for rule_loader module."""
import textwrap
from pathlib import Path

import pytest

from src.pdf_annotation_tool.rule_loader import load_rules
from src.pdf_annotation_tool.models import MarkType, MatchMode, Position


def test_load_single_tick_rule(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Tick Total Revenue"
            type: tick
            search: "Total Revenue"
            position: right
            match: all
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))

    assert len(rules) == 1
    rule = rules[0]
    assert rule.name == "Tick Total Revenue"
    assert rule.type == MarkType.TICK
    assert rule.search == "Total Revenue"
    assert rule.position == Position.RIGHT
    assert rule.match == MatchMode.ALL


def test_load_multiple_rules(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Rule A"
            type: tick
            search: "Total Revenue"
          - name: "Rule B"
            type: tick
            search: "Gross Profit"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert len(rules) == 2
    assert rules[0].search == "Total Revenue"
    assert rules[1].search == "Gross Profit"


def test_load_rules_defaults(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Minimal"
            type: tick
            search: "Net Income"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    rule = rules[0]
    assert rule.position == Position.RIGHT
    assert rule.match == MatchMode.ALL


def test_load_rules_empty_file_returns_empty_list(tmp_path: Path) -> None:
    rules_file = tmp_path / "empty.yaml"
    rules_file.write_text("")

    rules = load_rules(str(rules_file))
    assert rules == []


def test_load_rules_no_rules_key_returns_empty_list(tmp_path: Path) -> None:
    rules_file = tmp_path / "norules.yaml"
    rules_file.write_text("version: 1\n")

    rules = load_rules(str(rules_file))
    assert rules == []


# --- New mark types ---

def test_load_flag_rule(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Flag Net Income"
            type: flag
            search: "Net Income"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].type == MarkType.FLAG


def test_load_back_reference_rule(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Ref Total Equity"
            type: back_reference
            search: "Total Equity"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].type == MarkType.BACK_REFERENCE


def test_load_paragraph_end_rule(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Para End"
            type: paragraph_end
            search: "Cash Flow."
            position: flush_right
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].type == MarkType.PARAGRAPH_END
    assert rules[0].position == Position.FLUSH_RIGHT


# --- New positions ---

def test_load_position_left(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Left Mark"
            type: tick
            search: "Revenue"
            position: left
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].position == Position.LEFT


def test_load_position_above(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Above Mark"
            type: flag
            search: "Revenue"
            position: above
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].position == Position.ABOVE


def test_load_position_below(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Below Mark"
            type: flag
            search: "Revenue"
            position: below
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].position == Position.BELOW


# --- Match modes ---

def test_load_match_first(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "First Only"
            type: tick
            search: "Revenue"
            match: first
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].match == MatchMode.FIRST


def test_load_match_page(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Page 2 Only"
            type: tick
            search: "Revenue"
            match: "page:2"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].match == MatchMode.PAGE
    assert rules[0].match_page == 1  # 0-indexed internally


# --- Offsets ---

def test_load_offsets(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Offset Mark"
            type: tick
            search: "Revenue"
            offset_x: 5.0
            offset_y: -3.0
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].offset_x == 5.0
    assert rules[0].offset_y == -3.0


def test_load_offsets_default_zero(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "No Offset"
            type: tick
            search: "Revenue"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    rules = load_rules(str(rules_file))
    assert rules[0].offset_x == 0.0
    assert rules[0].offset_y == 0.0


# --- Invalid config rejection ---

def test_invalid_mark_type_raises(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Bad Type"
            type: invalid_mark_type
            search: "Revenue"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    with pytest.raises(ValueError):
        load_rules(str(rules_file))


def test_invalid_position_raises(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Bad Position"
            type: tick
            search: "Revenue"
            position: diagonal
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    with pytest.raises(ValueError):
        load_rules(str(rules_file))


def test_invalid_match_mode_raises(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "Bad Match"
            type: tick
            search: "Revenue"
            match: sometimes
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    with pytest.raises(ValueError):
        load_rules(str(rules_file))


def test_missing_name_raises(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - type: tick
            search: "Revenue"
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    with pytest.raises(KeyError):
        load_rules(str(rules_file))


def test_missing_search_raises(tmp_path: Path) -> None:
    yaml_content = textwrap.dedent("""\
        rules:
          - name: "No Search"
            type: tick
    """)
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(yaml_content)

    with pytest.raises(KeyError):
        load_rules(str(rules_file))
