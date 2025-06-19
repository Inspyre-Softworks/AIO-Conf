from __future__ import annotations

from typing import List
from ..core import OptionSpec, ConfigSpec


def build_option(name: str, type_: type, default=None, env=None, cli=None, required=False) -> OptionSpec:
    return OptionSpec(name=name, type=type_, default=default, env=env, cli=cli, required=required)


def build_config(options: List[OptionSpec]) -> ConfigSpec:
    return ConfigSpec(options)
