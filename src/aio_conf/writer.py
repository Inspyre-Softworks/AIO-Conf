from __future__ import annotations

from configparser import ConfigParser
from io import StringIO
from typing import Any, Dict


def to_ini(data: Dict[str, Any]) -> str:
    parser = ConfigParser()
    parser["DEFAULT"] = {k: str(v) for k, v in data.items()}
    buf = StringIO()
    parser.write(buf)
    return buf.getvalue()
