from __future__ import annotations

import json
from pathlib import Path
from ..core import ConfigSpec, OptionSpec


def dump_spec(spec: ConfigSpec, path: str | Path) -> None:
    data = {
        "options": [
            {
                "name": opt.name,
                "type": opt.type.__name__,
                "default": opt.default,
                "env": opt.env,
                "cli": opt.cli,
                "required": opt.required,
            }
            for opt in spec.options
        ]
    }
    Path(path).write_text(json.dumps(data, indent=2))
