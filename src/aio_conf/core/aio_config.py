from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .conf_spec import ConfigSpec
from ..loader import parse_cli, parse_env, load_file
from ..writer import to_ini


class AIOConfig:
    """
    All-in-one configuration class.

    Parameters:
        spec (ConfigSpec):
            The configuration specification that defines available options.

    Attributes:
        spec (ConfigSpec):
            The configuration specification instance.

        values (dict[str, Any]):
            A mapping of option names to their resolved values.

    Since:
        v1.0.0
    """

    def __init__(self, spec: ConfigSpec):
        self.spec = spec
        self.values: Dict[str, Any] = {opt.name: opt.default for opt in spec.options}

    @classmethod
    def load_from_spec(cls, path: str | Path) -> AIOConfig:
        """
        Load a configuration from a JSON spec file.

        Parameters:
            path (str | Path):
                Path to the JSON file defining the configuration specification.

        Returns:
            AIOConfig:
                New instance loaded from the provided spec file.

        Since:
            v1.0.0
        """
        spec = ConfigSpec.from_json_file(path)
        return cls(spec)

    def load(
        self,
        cli_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        file_path: Optional[str | Path] = None,
    ) -> None:
        """
        Load configuration values from CLI args, environment variables, and an optional file.

        Sources are merged in priority order:
            1. CLI arguments
            2. Environment variables
            3. File values
            4. Defaults from the spec

        Parameters:
            cli_args (Optional[list[str]]):
                CLI arguments to parse. If None, CLI args are skipped.

            env (Optional[dict[str, str]]):
                Environment variables to parse. Defaults to `os.environ`.

            file_path (Optional[str | Path]):
                Path to a config file. If None, file values are skipped.

        Returns:
            None

        Since:
            v1.0.0
        """
        env = env or os.environ
        cli_data = parse_cli(self.spec, cli_args or [])
        env_data = parse_env(self.spec, env)
        file_data = load_file(file_path) if file_path else {}

        self.values = merge_sources(self.spec, cli_data, env_data, file_data)

    def as_dict(self) -> Dict[str, Any]:
        """
        Get configuration as a dictionary.

        Returns:
            dict[str, Any]:
                Copy of the current configuration values.

        Since:
            v1.0.0
        """
        return dict(self.values)

    def save_ini(self, path: str | Path) -> None:
        """
        Save configuration values to an INI file.

        Parameters:
            path (str | Path):
                Destination path for the INI file.

        Returns:
            None

        Since:
            v1.0.0
        """
        text = to_ini(self.values)
        Path(path).write_text(text, encoding='utf-8')


def merge_sources(
    spec: ConfigSpec,
    cli: Dict[str, Any],
    env: Dict[str, Any],
    file: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge values from CLI, environment, and file sources based on the spec.

    Priority order:
        1. CLI arguments
        2. Environment variables
        3. File values
        4. Default value from spec

    Parameters:
        spec (ConfigSpec):
            The configuration specification.

        cli (dict[str, Any]):
            Parsed CLI arguments.

        env (dict[str, Any]):
            Parsed environment variables.

        file (dict[str, Any]):
            Parsed file values.

    Returns:
        dict[str, Any]:
            Merged dictionary of resolved configuration values.

    Since:
        v1.0.0
    """
    merged = {}
    for opt in spec.options:
        if opt.name in cli:
            merged[opt.name] = cli[opt.name]
        elif opt.name in env:
            merged[opt.name] = env[opt.name]
        elif opt.name in file:
            merged[opt.name] = file[opt.name]
        else:
            merged[opt.name] = opt.default

    return merged


__all__ = [
    'AIOConfig',
    'merge_sources',
]
