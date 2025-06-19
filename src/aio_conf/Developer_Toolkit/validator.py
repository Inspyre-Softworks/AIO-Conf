from __future__ import annotations

from ..core import ConfigSpec


def validate_spec(spec: ConfigSpec) -> None:
    names = set()
    for opt in spec.options:
        if opt.name in names:
            raise ValueError(f"Duplicate option: {opt.name}")
        names.add(opt.name)
        if opt.required and opt.default is None:
            raise ValueError(f"Required option {opt.name} has no default")
