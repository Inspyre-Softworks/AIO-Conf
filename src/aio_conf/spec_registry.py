"""Persistent discovery of configuration specification files."""

from __future__ import annotations

import json
from pathlib import Path

import platformdirs


APP_NAME = "aio-conf"
APP_AUTHOR = "Inspyre Softworks"
DEFAULT_SPEC_FILENAME = "config_spec.json"
SPEC_REGISTRY_FILENAME = "spec_files.json"


def default_spec_path() -> Path:
    """Return the platform-specific default path for a configuration spec."""
    return _config_directory() / DEFAULT_SPEC_FILENAME


def spec_registry_path() -> Path:
    """Return the platform-specific registry path for known spec files."""
    return _config_directory() / SPEC_REGISTRY_FILENAME


def track_spec(path: str | Path) -> Path:
    """Persist a canonical spec path and return it."""
    resolved = Path(path).expanduser().resolve()
    paths = load_tracked_specs()
    if resolved in paths:
        return resolved

    paths.append(resolved)
    registry = spec_registry_path()
    registry.parent.mkdir(parents=True, exist_ok=True)
    temporary = registry.with_suffix(f"{registry.suffix}.tmp")
    temporary.write_text(
        json.dumps({"spec_files": [str(item) for item in paths]}, indent=2),
        encoding="utf-8",
    )
    temporary.replace(registry)
    return resolved


def load_tracked_specs() -> list[Path]:
    """Load all known spec paths in insertion order."""
    registry = spec_registry_path()
    if not registry.exists():
        return []

    data = json.loads(registry.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("spec_files"), list):
        raise ValueError(f"Invalid registry format in {registry}")

    raw_paths = data["spec_files"]
    if not all(isinstance(item, str) for item in raw_paths):
        raise ValueError(f"Invalid spec file path in {registry}")
    return [Path(item) for item in raw_paths]


def _config_directory() -> Path:
    return platformdirs.user_config_path(APP_NAME, APP_AUTHOR)


__all__ = [
    "default_spec_path",
    "load_tracked_specs",
    "spec_registry_path",
    "track_spec",
]
