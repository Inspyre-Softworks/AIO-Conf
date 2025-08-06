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
from typing import Union, Optional

import json
from pathlib import Path
from aio_conf.core import ConfigSpec, OptionSpec


def dump_spec(
        spec: ConfigSpec,
        path: Union[str, Path],
        return_path_on_success: Optional[bool] = None
) -> Optional[str]:
    """
    Dump a ConfigSpecto a JSON file.

    Parameters:
        spec (configSpec:
            The ConfigSpec to dump.

        path (Union[str, Path]):
            The path to the file to dump to.

        return_path_on_success (Optional[bool]):
            If True, return the path to the file.

            Otherwise; return None.

    Returns:
        Optional[str]:
            The path to the file.

            If None, the file was not dumped, or :param:return_path_on_success is None or False.
    """
    data = {
        "options": [
            {
                "name":        opt.name,
                "type":        opt.type.__name__,
                "default":     opt.default,
                "env":         opt.env,
                "cli":         opt.cli,
                "required":    opt.required,
                "description": opt.description
            }
            for opt in spec.options
        ]
    }
    Path(path).write_text(json.dumps(data, indent=2))

    if return_path_on_success is not None and return_path_on_success:
        return path
    else:
        return None


del annotations, json, Path, Union, Optional, ConfigSpec, OptionSpec  # Clean up namespace

__all__ = ["dump_spec"]

