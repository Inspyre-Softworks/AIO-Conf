from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json
import yaml
import os
from pathlib import Path


@dataclass
class OptionSpec:
    def __init__(
        self,
        name:        str,
        value_type:  type,
        default:     Any                         = None,
        env:         Optional[str]               = None,
        cli:         Union[str, List[str], None] = None,
        required:    bool                        = False,
        description: str                         = "No description provided.",
    ):
        """
        Initialize an OptionSpec instance.

        Parameters:
            name (str):
                The name of the option.

            value_type (type):
                The type of the option.

            default (Any, optional):
                The default value of the option. Defaults to None.

            env (Optional[str], optional):
                The environment variable associated with the option. Defaults to None.

            cli (Union[str, List[str], None], optional):
                The command line argument(s) associated with the option. Defaults to None.

            required (bool, optional):
                Whether the option is required. Defaults to False.

            description (str, optional):
                A description of the option. Defaults to "No description provided."
        """
        self.name = name
        self.type = value_type
        self.default = default
        self.env = env
        self.required = required
        self.description = description

        if isinstance(cli, str):
            self.cli = [cli]
        elif isinstance(cli, list):
            self.cli = cli
        else:
            self.cli = None



@dataclass
class ConfigSpec:
    """
    Configuration specification.

    Since:
        v1.0.0
    """
    options: List[OptionSpec] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "ConfigSpec":
        """
        Load a configuration from a JSON file.

        Parameters:
            path (str | Path):
                The path to the file to load from.

        Returns:
            ConfigSpec:
                The configuration.

        Since:
            v1.0.0
        """
        with open(path, "r") as f:
            data = json.load(f)
        # Only keep keys that are fields of OptionSpec
        option_fields = {f.name for f in OptionSpec.__dataclass_fields__.values()}
        opts = [
            OptionSpec(**{k: v for k, v in opt.items() if k in option_fields})
            for opt in data.get("options", [])
        ]
        return cls(opts)

    def to_json_file(self, path: Union[str, Path], return_path_on_success: Optional[bool] = None) -> Optional[Union[str, Path]]:
        """
        Dump a ConfigSpec to a JSON file.

        Parameters:
           path (Union[str, Path]):
               The path to the file to dump to.

           return_path_on_success (Optional[bool]):
               If True, return the path to the file.

               Otherwise; return None.
        Returns:
               Optional[Union[str, Path]]:
                   The path to the file.

                   If None, the file was not dumped, or `return_path_on_success` is `None` or `False`.
       """
        from aio_conf.Developer_Toolkit.dumper import dump_spec
        rpos = return_path_on_success or False
        return dump_spec(self, path, return_path_on_success=rpos)


class AIOConfig:
    """
    All-in-one configuration class.

    Since:
        v1.0.0
    """
    def __init__(self, spec: ConfigSpec):
        self.spec = spec
        self.values: Dict[str, Any] = {opt.name: opt.default for opt in spec.options}

    @classmethod
    def load_from_spec(cls, path: str | Path) -> "AIOConfig":
        """
        Load a configuration from a JSON file.

        Parameters:
            path (str | Path):
                The path to the file to load from.

        Returns:
            AIOConfig:
                The configuration.

        Since:

        """
        spec = ConfigSpec.from_json_file(path)
        return cls(spec)

    def load(
            self,
            cli_args:  Optional[List[str]]      = None,
            env:       Optional[Dict[str, str]] = None,
            file_path: Optional[str | Path]     = None
    ) -> None:
        """
        Load the configuration from the command line arguments, environment variables, and a file.

        Parameters:
            cli_args (Optional[List[str]]):
                The command line arguments.

                If None, the command line arguments are not loaded

                Otherwise, the command line arguments are loaded.

            env (Optional[Dict[str, str]]):
                The environment variables.

                If None, the environment variables are not loaded

                Otherwise, the environment variables are loaded.

            file_path (Optional[str | Path]):
                The file path.

                If None, the file path is not loaded.

        Returns:
            None:
                The configuration is loaded.

        Since:
            v1.0.0
        """
        env = env or os.environ
        from .loader import parse_cli, parse_env, load_file
        cli_data = parse_cli(self.spec, cli_args or [])
        env_data = parse_env(self.spec, env)
        file_data = load_file(file_path) if file_path else {}
        self.values = merge_sources(self.spec, cli_data, env_data, file_data)

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.

        Returns:
            Dict[str, Any]:
                The configuration as a dictionary.

        Since:
            v1.0.0
        """
        return dict(self.values)

    def save_ini(self, path: str | Path) -> None:
        """
        Save the configuration to an INI file.

        Parameters:
            path (str | Path):
                The path to the file to save to.

        Returns:
            None:
                The configuration is saved.

        Since:
            v1.0.0
        """
        from .writer import to_ini
        text = to_ini(self.values)
        Path(path).write_text(text)


def merge_sources(spec: ConfigSpec, cli: Dict[str, Any], env: Dict[str, Any], file: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge the sources into a single dictionary.

    Parameters:
        spec (ConfigSpec):
            The configuration specification.

        cli (Dict[str, Any]):
            The command line arguments.

        env (Dict[str, Any]):
            The environment variables.

        file (Dict[str, Any]):
            The file data.

    Returns:
        Dict[str, Any]:
            The merged dictionary.

        If the option is not found in any of the sources, the default value is used.

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
