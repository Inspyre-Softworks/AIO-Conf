"""Unified configuration loader for Python applications.

This module provides classes to define configuration options and load them
from multiple sources. Configuration values are resolved in the following
order of precedence:

1. Command line arguments
2. Environment variables
3. User supplied configuration files (JSON/YAML/INI)
4. Default values defined in :class:`OptionSpec`

The :class:`AIOConfig` class exposes the merged result via :py:meth:`as_dict`
and can persist it to an INI file using :py:meth:`save_ini`.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
import argparse
import configparser
import json
import os
import builtins
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

try:  # Optional PyYAML dependency
    import yaml
except Exception:  # pragma: no cover - PyYAML might not be installed
    yaml = None


@dataclass
class OptionSpec:
    """Specification of a single configuration option."""

    name: str
    type: type = str
    default: Any = None
    env_var: Optional[str] = None
    cli_arg: Optional[str] = None
    help: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.__name__,
            "default": self.default,
            "env_var": self.env_var,
            "cli_arg": self.cli_arg,
            "help": self.help,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptionSpec":
        typ_name = data.get("type", "str")
        typ = getattr(builtins, typ_name, str)
        return cls(
            name=data["name"],
            type=typ,
            default=data.get("default"),
            env_var=data.get("env_var"),
            cli_arg=data.get("cli_arg"),
            help=data.get("help", ""),
        )


@dataclass
class ConfigSpec:
    """Collection of options and nested configuration sections."""

    options: Dict[str, OptionSpec] = field(default_factory=dict)
    subconfigs: Dict[str, "ConfigSpec"] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "options": {k: v.to_dict() for k, v in self.options.items()},
            "subconfigs": {k: v.to_dict() for k, v in self.subconfigs.items()},
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSpec":
        options = {
            name: OptionSpec.from_dict({"name": name, **spec})
            for name, spec in data.get("options", {}).items()
        }
        subconfigs = {
            name: cls.from_dict(spec)
            for name, spec in data.get("subconfigs", {}).items()
        }
        return cls(options=options, subconfigs=subconfigs)


def _iter_options(spec: ConfigSpec, path: Optional[List[str]] = None) -> Iterator[tuple[List[str], OptionSpec]]:
    path = path or []
    for name, opt in spec.options.items():
        yield path + [name], opt
    for sec_name, sub in spec.subconfigs.items():
        yield from _iter_options(sub, path + [sec_name])


def _set_nested(target: Dict[str, Any], path: Iterable[str], value: Any) -> None:
    path = list(path)
    for key in path[:-1]:
        target = target.setdefault(key, {})
    target[path[-1]] = value


def _merge_dict(base: Dict[str, Any], other: Dict[str, Any]) -> None:
    for key, value in other.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _merge_dict(base[key], value)
        else:
            base[key] = value


class AIOConfig:
    """Load configuration from CLI, environment variables and files."""

    def __init__(
        self,
        spec: ConfigSpec,
        *,
        cli_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        config_files: Optional[List[str | os.PathLike[str]]] = None,
    ) -> None:
        self.spec = spec
        self.env = env if env is not None else os.environ
        self.cli_args = cli_args or []
        self.config_files = [Path(p) for p in (config_files or [])]

        # Start with defaults
        self.config = self._build_defaults(spec)

        # Merge file values
        for path in self.config_files:
            _merge_dict(self.config, self._load_file(path))

        # Merge environment values
        _merge_dict(self.config, self._load_env())

        # Merge CLI values
        _merge_dict(self.config, self._load_cli())

    # ------------------------------------------------------------------ utils
    def _build_defaults(self, spec: ConfigSpec) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name, opt in spec.options.items():
            result[name] = opt.default
        for sec_name, sub in spec.subconfigs.items():
            result[sec_name] = self._build_defaults(sub)
        return result

    def _apply_types(self, data: Dict[str, Any], spec: ConfigSpec, path: Optional[List[str]] = None) -> Dict[str, Any]:
        path = path or []
        typed: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict) and key in spec.subconfigs:
                typed[key] = self._apply_types(value, spec.subconfigs[key], path + [key])
            elif key in spec.options:
                opt = spec.options[key]
                if isinstance(value, str) and opt.type is bool:
                    typed[key] = value.lower() in {"1", "true", "yes", "on"}
                else:
                    typed[key] = opt.type(value)
            else:
                typed[key] = value
        return typed

    # --------------------------------------------------------------- load file
    def _load_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        if path.suffix in {".json"}:
            with path.open() as f:
                data = json.load(f)
            return self._apply_types(data, self.spec)
        if path.suffix in {".yml", ".yaml"} and yaml is not None:
            with path.open() as f:
                data = yaml.safe_load(f) or {}
            return self._apply_types(data, self.spec)
        if path.suffix == ".ini":
            cp = configparser.ConfigParser()
            cp.read(path)
            data: Dict[str, Any] = {
                sec: {k: v for k, v in cp._sections.get(sec, {}).items() if k != "__name__"}
                for sec in cp.sections()
            }
            if cp.defaults():
                data.update(cp.defaults())
            return self._apply_types(data, self.spec)
        return {}

    # ------------------------------------------------------------- load env var
    def _load_env(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for path, opt in _iter_options(self.spec):
            if opt.env_var and opt.env_var in self.env:
                raw = self.env[opt.env_var]
                value = self._cast(raw, opt.type)
                _set_nested(result, path, value)
        return result

    # -------------------------------------------------------------- load cli
    def _load_cli(self) -> Dict[str, Any]:
        parser = argparse.ArgumentParser(add_help=False)
        for path, opt in _iter_options(self.spec):
            if opt.cli_arg:
                dest = "__".join(path)
                parser.add_argument(opt.cli_arg, dest=dest, type=opt.type, help=opt.help)
        ns, _ = parser.parse_known_args(self.cli_args)
        result: Dict[str, Any] = {}
        for dest, value in vars(ns).items():
            if value is not None:
                path = dest.split("__")
                _set_nested(result, path, value)
        return result

    @staticmethod
    def _cast(value: str, typ: type) -> Any:
        if typ is bool:
            return value.lower() in {"1", "true", "yes", "on"}
        return typ(value)

    # --------------------------------------------------------------- public API
    def as_dict(self) -> Dict[str, Any]:
        return self.config

    def save_ini(self, path: str | os.PathLike[str]) -> None:
        cp = configparser.ConfigParser()
        root_options = {k: v for k, v in self.config.items() if not isinstance(v, dict)}
        if root_options:
            cp["DEFAULT"] = {k: str(v) for k, v in root_options.items()}
        for section, values in self.config.items():
            if isinstance(values, dict):
                cp[section] = {k: str(v) for k, v in values.items()}
        with open(path, "w") as f:
            cp.write(f)


# ----------------------------------------------------------------- developer toolkit
# The developer toolkit simply exposes helpers for serialising specs to/from JSON.

class DeveloperToolkit:
    @staticmethod
    def spec_to_json(spec: ConfigSpec, path: str | os.PathLike[str]) -> None:
        with open(path, "w") as f:
            json.dump(spec.to_dict(), f, indent=2)

    @staticmethod
    def spec_from_json(path: str | os.PathLike[str]) -> ConfigSpec:
        with open(path) as f:
            data = json.load(f)
        return ConfigSpec.from_dict(data)


__all__ = [
    "OptionSpec",
    "ConfigSpec",
    "AIOConfig",
    "DeveloperToolkit",
]
