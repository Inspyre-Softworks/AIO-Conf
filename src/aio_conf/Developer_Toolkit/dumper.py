"""
Contains functions for dumping a ConfigSpec to a JSON file.

Author:
    Taylor-Jayde Blackstone

Since:
    v1.0.0

Functions:
    dump_spec
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import json

from aio_conf.core import ConfigSpec, OptionSpec


def dump_spec(
    spec: ConfigSpec,
    path: Union[str, Path],
    return_path_on_success: Optional[bool] = None,
    *,
    indent: int = 2,
    sort_keys: bool = True,
) -> Optional[Path]:
    """
    Dump a ConfigSpec to a JSON file.

    Parameters:
        spec (ConfigSpec):
            The ConfigSpec to dump.

        path (str | Path):
            The path to the file to dump to.

        return_path_on_success (Optional[bool]):
            If True, return the path to the file. Otherwise, return None.

        indent (int):
            Indentation level for JSON pretty printing. Defaults to 2.

        sort_keys (bool):
            Whether to sort JSON object keys. Defaults to True.

    Returns:
        Optional[pathlib.Path]:
            The path to the file if `return_path_on_success` is True; otherwise None.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'options': [
            {
                'name':        opt.name,
                'type':        _type_to_string(opt),
                'default':     opt.default,
                'env':         opt.env,
                'cli':         opt.cli,
                'required':    opt.required,
                'description': opt.description,
            }
            for opt in spec.options
        ]
    }

    p.write_text(json.dumps(data, indent=indent, sort_keys=sort_keys), encoding='utf-8')
    return p if return_path_on_success else None


# ---------- Helpers ----------

def _type_to_string(opt: OptionSpec) -> str:
    """
    Convert OptionSpec.type to a stable string.

    - If it's a builtin/typing-friendly type (int, float, bool, str, Path), use __name__ or 'Path'.
    - If it's already a string (e.g., 'int', 'bool', 'path'), return it as-is.
    - If it's another callable, fall back to its __name__ when available; otherwise repr().
    """
    t = getattr(opt, 'type', None)

    if isinstance(t, str):
        return t

    if t is None:
        return 'str'

    # pathlib.Path special-case for readability
    if t is Path:
        return 'Path'

    # Normal types and most callables have __name__
    name = getattr(t, '__name__', None)
    if isinstance(name, str):
        return name

    # Last resort: repr the callable/type
    return repr(t)


__all__ = ['dump_spec']
