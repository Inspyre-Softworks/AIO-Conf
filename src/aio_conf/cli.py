from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

import yaml

from .core import ConfigSpec
from .spec_registry import default_spec_path, load_tracked_specs, track_spec
from .writer import to_ini


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aio-conf",
        description="Swiss army knife for AIO-Conf specifications.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser(
        "init",
        help="Generate a starter configuration spec",
    )
    init_cmd.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Where to write the new spec file (defaults to the platform user config directory)",
    )
    init_cmd.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the file if it already exists",
    )

    validate_cmd = sub.add_parser(
        "validate",
        help="Validate a configuration spec",
    )
    validate_cmd.add_argument("spec", type=Path, help="Path to the JSON spec file")

    sample_cmd = sub.add_parser(
        "sample",
        help="Generate a sample configuration file from the spec",
    )
    sample_cmd.add_argument("spec", type=Path, help="Path to the JSON spec file")
    sample_cmd.add_argument(
        "--format",
        default="yaml",
        choices=["yaml", "json", "toml", "ini"],
        help="Output format for the sample file",
    )
    sample_cmd.add_argument(
        "--output",
        type=Path,
        help="Optional file path. Defaults to stdout if omitted.",
    )

    sub.add_parser(
        "list",
        help="List tracked configuration spec file locations",
    )

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "init":
        return _cmd_init(args.path, force=args.force)
    if args.command == "validate":
        return _cmd_validate(args.spec)
    if args.command == "sample":
        return _cmd_sample(args.spec, fmt=args.format, output=args.output)
    if args.command == "list":
        return _cmd_list()
    parser.error("Congratulations, you found an impossible branch.")
    return 2


def _cmd_init(path: Path | None, *, force: bool) -> int:
    path = default_spec_path() if path is None else path
    template = {
        "options": [
            {
                "name": "app_name",
                "type": "str",
                "default": "my-app",
                "description": "Human readable application name.",
                "env": "APP_NAME",
                "cli": ["--app-name"],
            },
            {
                "name": "debug",
                "type": "bool",
                "default": False,
                "description": "Enable developer friendly behaviour.",
                "env": "APP_DEBUG",
                "cli": ["--debug"],
            },
        ]
    }
    if path.exists() and not force:
        print(f"Nope. {path} already exists. Pass --force if you really mean it.")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    if not _track_or_report(path):
        return 1
    print(f"Created starter spec at {path}")
    return 0


def _cmd_validate(path: Path) -> int:
    try:
        ConfigSpec.from_json_file(path)
    except Exception as exc:  # pragma: no cover - exercised via tests
        print(f"Spec check failed spectacularly: {exc}")
        return 1
    print("Spec looks good. Gold star achieved!")
    return 0


def _cmd_sample(path: Path, *, fmt: str, output: Path | None) -> int:
    try:
        spec = ConfigSpec.from_json_file(path)
    except Exception as exc:
        print(f"Couldn't read that spec: {exc}")
        return 1

    sample = _defaults_from_spec(spec)
    try:
        text = _render_sample(sample, fmt)
    except ValueError as exc:
        print(str(exc))
        return 1

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Sample configuration written to {output}")
    else:
        print(text)
    return 0


def _cmd_list() -> int:
    try:
        paths = load_tracked_specs()
    except (OSError, ValueError) as exc:
        print(f"Couldn't read the spec file registry: {exc}")
        return 1

    if not paths:
        print("No configuration spec files have been tracked yet.")
        return 0

    print("Tracked configuration spec files:")
    for path in paths:
        missing = " [missing]" if not path.is_file() else ""
        print(f"- {path}{missing}")
    return 0


def _track_or_report(path: Path) -> bool:
    try:
        track_spec(path)
    except (OSError, ValueError) as exc:
        print(f"Couldn't update the spec file registry: {exc}")
        return False
    return True


def _defaults_from_spec(spec: ConfigSpec) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {}
    for opt in spec.options:
        type_name = opt.type if isinstance(opt.type, str) else getattr(opt.type, "__name__", str(opt.type))
        defaults[opt.name] = opt.default if opt.default is not None else f"<{type_name}>"
    return defaults


def _render_sample(data: Dict[str, Any], fmt: str) -> str:
    fmt = fmt.lower()
    if fmt == "yaml":
        return yaml.safe_dump(data, sort_keys=False)
    if fmt == "json":
        return json.dumps(data, indent=2)
    if fmt == "ini":
        return to_ini(data)
    if fmt == "toml":
        return _to_toml(data)
    raise ValueError(f"Unknown format '{fmt}'")


def _to_toml(data: Dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"[{key}]")
            for inner_key, inner_value in value.items():
                lines.append(f"{inner_key} = {_toml_repr(inner_value)}")
        else:
            lines.append(f"{key} = {_toml_repr(value)}")
    return "\n".join(lines) + "\n"


def _toml_repr(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        inner = ", ".join(f"{k} = {_toml_repr(v)}" for k, v in value.items())
        return f"{{{inner}}}"
    if isinstance(value, (list, tuple, set)):
        inner = ", ".join(_toml_repr(v) for v in value)
        return f"[{inner}]"
    if value is None:
        raise ValueError("TOML does not support null values")
    return json.dumps(str(value))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
