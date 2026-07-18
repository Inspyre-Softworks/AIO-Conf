from __future__ import annotations

from configparser import ConfigParser
from io import StringIO
import json
from typing import Any, Dict


def to_ini(data: Dict[str, Any]) -> str:
    parser = ConfigParser(interpolation=None)
    parser.optionxform = str
    parser["DEFAULT"] = {
        key: _format_value(value)
        for key, value in data.items()
        if not isinstance(value, dict)
    }
    for key, value in data.items():
        if isinstance(value, dict):
            parser[key] = {
                inner_key: _format_value(inner_value)
                for inner_key, inner_value in value.items()
            }
    buf = StringIO()
    parser.write(buf)
    return buf.getvalue()


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value)
    return str(value)
