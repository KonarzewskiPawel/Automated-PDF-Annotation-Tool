"""Domain models for the PDF annotation tool."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MarkType(Enum):
    TICK = "tick"
    FLAG = "flag"
    BACK_REFERENCE = "back_reference"
    PARAGRAPH_END = "paragraph_end"
    BADGE = "badge"
    SHADING_BADGE = "shading_badge"


class Position(Enum):
    RIGHT = "right"
    LEFT = "left"
    ABOVE = "above"
    BELOW = "below"
    FLUSH_RIGHT = "flush_right"


class MatchMode(Enum):
    ALL = "all"
    FIRST = "first"
    PAGE = "page"


@dataclass
class PluginResult:
    text: str
    color: tuple[float, float, float]
    mark_type: MarkType


@dataclass
class Rule:
    name: str
    search: str
    type: MarkType | None = None
    plugin: str | None = None
    position: Position = Position.RIGHT
    match: MatchMode = MatchMode.ALL
    match_page: int | None = None  # 0-indexed page number; used when match == PAGE
    offset_x: float = 0.0
    offset_y: float = 0.0
    fill_color: str | None = None   # "amber", "red", or "yellow" — for SHADING_BADGE
    badge_text: str | None = None   # static text for SHADING_BADGE


@dataclass
class RuleVerificationResult:
    rule_name: str
    status: str  # "PASS" or "FAIL"
    annotations_found: int


@dataclass
class VerificationResult:
    rule_results: list[RuleVerificationResult]
    passed: bool
    total_annotations: int


@dataclass
class AnnotationResult:
    input_path: str
    output_path: str
    marks_placed: int
    details: list[dict[str, object]] = field(default_factory=list)
    verification: VerificationResult | None = None
