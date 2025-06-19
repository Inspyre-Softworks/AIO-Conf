from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import yaml
import os
from pathlib import Path


@dataclass
class OptionSpec:
    name: str
    type: type
    default: Any = None
    env: Optional[str] = None
    cli: Optional[str] = None
    required: bool = False


@dataclass
class ConfigSpec:
    options: List[OptionSpec] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | Path) -> "ConfigSpec":
        with open(path, "r") as f:
            data = json.load(f)
        opts = [OptionSpec(**opt) for opt in data.get("options", [])]
        return cls(opts)


class AIOConfig:
    def __init__(self, spec: ConfigSpec):
        self.spec = spec
        self.values: Dict[str, Any] = {opt.name: opt.default for opt in spec.options}

    @classmethod
    def load_from_spec(cls, path: str | Path) -> "AIOConfig":
        spec = ConfigSpec.from_json(path)
        return cls(spec)

    def load(self, cli_args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None,
             file_path: Optional[str | Path] = None) -> None:
        env = env or os.environ
        from .loader import parse_cli, parse_env, load_file
        cli_data = parse_cli(self.spec, cli_args or [])
        env_data = parse_env(self.spec, env)
        file_data = load_file(file_path) if file_path else {}
        self.values = merge_sources(self.spec, cli_data, env_data, file_data)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.values)

    def save_ini(self, path: str | Path) -> None:
        from .writer import to_ini
        text = to_ini(self.values)
        Path(path).write_text(text)


def merge_sources(spec: ConfigSpec, cli: Dict[str, Any], env: Dict[str, Any], file: Dict[str, Any]) -> Dict[str, Any]:
    merged = {}
    for opt in spec.options:
        if opt.name in cli:
            merged[opt.name] = cli[opt.name]
        elif opt.name in env:
            merged[opt.name] = env[opt.name]
        elif opt.name in file:
            merged[opt.name] = file[opt.name]
        else:
            merged[opt.name] = opt.default
    return merged
