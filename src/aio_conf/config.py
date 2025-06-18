from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import json
import os
from typing import Any, Sequence, Mapping


@dataclass
class OptionSpec:
    """Specification for a single configuration option."""

    name: str
    default: Any = None
    env: str | None = None
    cli: str | None = None


@dataclass
class ConfigSpec:
    """Collection of option specifications.

    A spec may also define sub-specs for subcommands.
    """

    options: Sequence[OptionSpec] = field(default_factory=list)
    subcommands: Mapping[str, 'ConfigSpec'] = field(default_factory=dict)


class AIOConfig:
    """Load configuration values from multiple sources in priority order."""

    def __init__(
        self,
        spec: ConfigSpec,
        config_file: str | Path | None = None,
        argv: Sequence[str] | None = None,
        *,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        self.spec = spec
        self.config_file = Path(config_file) if config_file else None
        self.argv = list(argv) if argv is not None else None
        self._values: dict[str, Any] = {}
        self.subconfigs: dict[str, AIOConfig] = {}
        self._load(data)

    def _load(self, data: Mapping[str, Any] | None = None) -> None:
        if data is not None:
            config_data: dict[str, Any] = dict(data)
        else:
            config_data = {}
            if self.config_file and self.config_file.exists():
                with open(self.config_file, "r", encoding="utf8") as fh:
                    try:
                        config_data = json.load(fh)
                    except json.JSONDecodeError:
                        # Silently ignore invalid json
                        config_data = {}

        parser = argparse.ArgumentParser(add_help=False)
        for opt in self.spec.options:
            if opt.cli:
                parser.add_argument(opt.cli, dest=opt.name)

        args, _ = parser.parse_known_args(self.argv)
        arg_dict = vars(args)

        for opt in self.spec.options:
            value = None
            if opt.cli and arg_dict.get(opt.name) is not None:
                value = arg_dict[opt.name]
            elif opt.env and opt.env in os.environ:
                value = os.environ[opt.env]
            elif opt.name in config_data:
                value = config_data[opt.name]
            else:
                value = opt.default

            self._values[opt.name] = value

        for name, subspec in self.spec.subcommands.items():
            subdata = config_data.get(name, {}) if isinstance(config_data, dict) else {}
            subcfg = AIOConfig(
                subspec,
                config_file=self.config_file,
                argv=self.argv,
                data=subdata,
            )
            self.subconfigs[name] = subcfg

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple delegation
        try:
            return self._values[name]
        except KeyError as exc:  # pragma: no cover - simple delegation
            raise AttributeError(name) from exc

    def get(self, name: str, default: Any = None) -> Any:
        return self._values.get(name, default)

    def for_subcommand(self, name: str) -> 'AIOConfig':
        return self.subconfigs[name]

    def __repr__(self) -> str:  # pragma: no cover - simple representation
        return f"AIOConfig({self._values!r})"
