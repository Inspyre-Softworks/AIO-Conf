from __future__ import annotations
from typing import Any, Dict, List

from .. import parse_cli


class ConfigCLIParser:
    """
    Build and parse CLI args from a ConfigSpec.

    Parameters:
        spec:
            The ConfigSpec instance with `.options` iterable.
            Each option should expose fields like:
              - name (str): canonical destination name
              - cli (str | Iterable[str] | None): e.g., "--log-level" or ["-l", "--log-level"]
              - type (type | callable | None): e.g., bool, int, float, str, Path, custom callable
              - nargs (str | int | None): e.g., '?', '*', '+', or an int
              - choices (Iterable | None): valid values
              - default (Any | None)
              - required (bool | None)
              - metavar (str | None)
              - help (str | None)

        allow_boolean_negation (bool):
            If True, boolean flags accept both --flag / --no-flag via BooleanOptionalAction.

    Methods:
        parse(args: List[str]) -> Dict[str, Any]:
            Parse CLI `args` and return a dict of only the options explicitly provided
            (i.e., excluding keys whose values are None).

    Example Usage:
        parser = ConfigCLIParser(spec)
        values = parser.parse(["--verbose", "--retries", "3"])
    """

    def __init__(self, spec, *, allow_boolean_negation: bool = True):
        self._spec = spec
        self._allow_boolean_negation = allow_boolean_negation

    def parse(self, args: List[str]) -> Dict[str, Any]:
        return parse_cli(
            self._spec,
            args,
            allow_boolean_negation=self._allow_boolean_negation,
        )
