"""Tests for plugin auto-discovery registry."""
from __future__ import annotations

from pathlib import Path

from src.pdf_annotation_tool.models import MarkType, PluginResult
from src.pdf_annotation_tool.plugin_registry import get_plugin, load_plugins, reset_registry


def _write_plugin(tmp_path: Path, name: str, body: str) -> Path:
    f = tmp_path / f"{name}.py"
    f.write_text(body)
    return f


def test_load_plugins_discovers_compute_function(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        "my_plugin",
        "from src.pdf_annotation_tool.models import PluginResult, MarkType\n"
        "def compute(text, config):\n"
        "    return PluginResult(text='OK', color=(0,1,0), mark_type=MarkType.BADGE)\n",
    )
    registry = load_plugins(tmp_path)
    assert "my_plugin" in registry


def test_load_plugins_skips_init(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "__init__", "# empty\n")
    registry = load_plugins(tmp_path)
    assert "__init__" not in registry


def test_load_plugins_skips_file_without_compute(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "no_compute", "x = 1\n")
    registry = load_plugins(tmp_path)
    assert "no_compute" not in registry


def test_load_plugins_returns_callable(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        "stub",
        "from src.pdf_annotation_tool.models import PluginResult, MarkType\n"
        "def compute(text, config):\n"
        "    return PluginResult(text='T', color=(1,0,0), mark_type=MarkType.BADGE)\n",
    )
    registry = load_plugins(tmp_path)
    result = registry["stub"]("some text", {})
    assert isinstance(result, PluginResult)
    assert result.text == "T"


def test_load_plugins_empty_dir(tmp_path: Path) -> None:
    registry = load_plugins(tmp_path)
    assert registry == {}


def test_load_plugins_real_plugins_dir_has_gp_percentage() -> None:
    """The real src/plugins/ directory contains gp_percentage."""
    plugins_dir = Path(__file__).parent.parent / "src" / "plugins"
    registry = load_plugins(plugins_dir)
    assert "gp_percentage" in registry


def test_get_plugin_returns_callable_for_known_plugin() -> None:
    reset_registry()
    compute = get_plugin("gp_percentage")
    assert compute is not None and callable(compute)
    reset_registry()


def test_get_plugin_returns_none_for_unknown_plugin() -> None:
    reset_registry()
    assert get_plugin("does_not_exist") is None
    reset_registry()


def test_get_plugin_caches_registry_across_calls() -> None:
    reset_registry()
    first = get_plugin("gp_percentage")
    second = get_plugin("gp_percentage")
    assert first is second
    reset_registry()
