from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping

import json
from configparser import ConfigParser

import yaml

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    tomllib = None  # type: ignore[assignment]

from ..core import ConfigSpec
from ..core.opt_spec import OptionSpec, _infer_scalar


class UnknownFileFormatError(RuntimeError):
    """Raised when no loader is registered for a file extension."""


@dataclass(slots=True)
class FileLoader:
    """Simple file-loader wrapper used by :class:`LoaderRegistry`."""

    suffixes: tuple[str, ...]

    def load(self, path: Path) -> dict[str, Any]:  # pragma: no cover - interface stub
        raise NotImplementedError


class LoaderRegistry:
    """Registry for mapping file extensions to loader implementations."""

    def __init__(self) -> None:
        self._loaders: dict[str, FileLoader] = {}

    def register(self, loader: FileLoader) -> None:
        for suffix in loader.suffixes:
            normalized = suffix.lower()
            self._loaders[normalized] = loader

    def load(self, path: Path) -> dict[str, Any]:
        suffix = path.suffix.lower()
        loader = self._loaders.get(suffix)
        if loader is None:
            raise UnknownFileFormatError(f"No loader registered for '{suffix}'")
        return loader.load(path)


class JsonLoader(FileLoader):
    suffixes = (".json",)

    def load(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        return json.loads(text or "{}")


class YamlLoader(FileLoader):
    suffixes = (".yaml", ".yml")

    def load(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return data or {}


class TomlLoader(FileLoader):
    suffixes = (".toml",)

    def load(self, path: Path) -> dict[str, Any]:
        if tomllib is None:
            raise RuntimeError("tomllib is unavailable; cannot parse TOML files")
        with path.open("rb") as fp:
            data = tomllib.load(fp)
        return data or {}


class IniLoader(FileLoader):
    suffixes = (".ini", ".cfg")

    def load(self, path: Path) -> dict[str, Any]:
        parser = ConfigParser()
        parser.read(path, encoding="utf-8")
        return _configparser_to_dict(parser)


def _configparser_to_dict(parser: ConfigParser) -> dict[str, Any]:
    data: dict[str, Any] = {}
    defaults = {k: _infer_scalar(v) for k, v in parser.defaults().items()}
    data.update(defaults)
    for section in parser.sections():
        items = {k: _infer_scalar(v) for k, v in parser[section].items()}
        if section.lower() == "default":
            data.update(items)
        else:
            data[section] = items
    return data


_registry = LoaderRegistry()
_registry.register(JsonLoader(JsonLoader.suffixes))
_registry.register(YamlLoader(YamlLoader.suffixes))
if tomllib is not None:
    _registry.register(TomlLoader(TomlLoader.suffixes))
_registry.register(IniLoader(IniLoader.suffixes))


def get_registry() -> LoaderRegistry:
    """Return the global loader registry."""

    return _registry


def register_loader(loader: FileLoader) -> None:
    """Register a custom file loader globally."""

    _registry.register(loader)


def parse_cli(spec: ConfigSpec, args: Iterable[str]) -> Dict[str, Any]:
    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    for opt in spec.options:
        if opt.cli:
            kwargs: Dict[str, Any] = {"dest": opt.name}
            opt_type = opt.type
            if opt_type is bool or (isinstance(opt_type, str) and str(opt_type).lower() == "bool"):
                kwargs["action"] = "store_true"
            else:
                kwargs["type"] = opt.coerce
            flags = opt.cli if isinstance(opt.cli, (list, tuple)) else [opt.cli]
            if flags:
                parser.add_argument(*[flag for flag in flags if flag], **kwargs)
    parsed, _ = parser.parse_known_args(list(args))
    return {k: v for k, v in vars(parsed).items() if v is not None}


def parse_env(spec: ConfigSpec, env: MutableMapping[str, str]) -> Dict[str, Any]:
    resolved: Dict[str, Any] = {}
    for opt in spec.options:
        if not opt.env:
            continue
        base_key = opt.env
        nested_prefix = f"{base_key}__"
        direct_value = env.get(base_key)
        nested_pairs = {k: v for k, v in env.items() if k.startswith(nested_prefix)}
        if direct_value is not None:
            try:
                resolved[opt.name] = opt.coerce(direct_value)
            except ValueError as exc:
                raise ValueError(f"Environment variable '{base_key}' is invalid: {exc}") from exc
            continue
        if nested_pairs:
            nested_dict = _build_nested_dict(nested_pairs, nested_prefix)
            if _expects_mapping(opt):
                resolved[opt.name] = opt.coerce(nested_dict)
            else:
                resolved[opt.name] = nested_dict
    return resolved


def _expects_mapping(opt: OptionSpec) -> bool:
    expected = opt.type
    if isinstance(expected, str):
        return expected.lower() == "dict"
    return expected is dict


def _build_nested_dict(pairs: Dict[str, str], prefix: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    for env_key, raw_value in pairs.items():
        path = env_key[len(prefix) :]
        segments = [segment for segment in path.split("__") if segment]
        if not segments:
            continue
        cursor: Dict[str, Any] = root
        for segment in segments[:-1]:
            cursor = cursor.setdefault(_normalize_env_key(segment), {})  # type: ignore[assignment]
        cursor[_normalize_env_key(segments[-1])] = _infer_scalar(raw_value)
    return root


def _normalize_env_key(segment: str) -> str:
    return segment.strip().lower().replace("-", "_")


def load_file(path: str | Path | None) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists() or not p.is_file():
        return {}
    try:
        return _registry.load(p)
    except UnknownFileFormatError:
        return {}


__all__ = [
    "FileLoader",
    "LoaderRegistry",
    "UnknownFileFormatError",
    "get_registry",
    "register_loader",
    "parse_cli",
    "parse_env",
    "load_file",
]
