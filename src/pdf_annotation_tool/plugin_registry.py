"""Auto-discovery and registry for PDF annotation plugins."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable

from src.pdf_annotation_tool.models import PluginResult

# Default plugins directory alongside src/pdf_annotation_tool/
_DEFAULT_PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


def load_plugins(plugins_dir: Path | None = None) -> dict[str, Callable[..., PluginResult]]:
    """Scan plugins_dir for .py files that expose a compute() function.

    Returns a mapping of plugin name (filename stem) to its compute callable.
    """
    if plugins_dir is None:
        plugins_dir = _DEFAULT_PLUGINS_DIR

    registry: dict[str, Callable[..., PluginResult]] = {}
    for py_file in sorted(plugins_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        if callable(getattr(module, "compute", None)):
            registry[py_file.stem] = module.compute
    return registry


_registry: dict[str, Callable[..., PluginResult]] | None = None


def get_plugin(name: str) -> Callable[..., PluginResult] | None:
    """Return the compute callable for the named plugin, or None if not found."""
    global _registry
    if _registry is None:
        _registry = load_plugins()
    return _registry.get(name)


def reset_registry() -> None:
    """Clear the cached registry (useful for testing)."""
    global _registry
    _registry = None
