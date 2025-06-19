from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .core import ConfigSpec


def parse_cli(spec: ConfigSpec, args: List[str]) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(add_help=False)
    for opt in spec.options:
        if opt.cli:
            parser.add_argument(opt.cli, dest=opt.name, type=opt.type)
    parsed, _ = parser.parse_known_args(args)
    return {k: v for k, v in vars(parsed).items() if v is not None}


def parse_env(spec: ConfigSpec, env: Dict[str, str]) -> Dict[str, Any]:
    result = {}
    for opt in spec.options:
        if opt.env and opt.env in env:
            result[opt.name] = opt.type(env[opt.env])
    return result


def load_file(path: str | Path) -> Dict[str, Any]:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    text = path.read_text()
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text) or {}
    elif path.suffix == ".json":
        data = json.loads(text)
    else:
        data = {}
    return data
