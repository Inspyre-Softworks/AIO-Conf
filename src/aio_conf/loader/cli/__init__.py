from __future__ import annotations
from argparse import ArgumentParser, BooleanOptionalAction
from typing import Any, Dict, Iterable, List, Optional


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
        self._parser = ArgumentParser(add_help=False)
        self._build()

    @staticmethod
    def _normalize_cli(cli) -> List[str]:
        if not cli:
            return []
        if isinstance(cli, (list, tuple)):
            return [str(x) for x in cli]
        return [str(cli)]

    def _build(self) -> None:
        for opt in getattr(self._spec, "options", []):
            flags = self._normalize_cli(getattr(opt, "cli", None))
            if not flags:
                # No CLI exposure for this option; skip.
                continue

            dest = getattr(opt, "name")
            opt_type = getattr(opt, "type", None)

            kwargs: Dict[str, Any] = {
                "dest": dest,
                "help": getattr(opt, "help", None),
                "default": getattr(opt, "default", None),
                "required": getattr(opt, "required", False),
                "choices": getattr(opt, "choices", None),
                "metavar": getattr(opt, "metavar", None),
            }
            # Strip None so argparse doesn’t get junk
            kwargs = {k: v for k, v in kwargs.items() if v is not None}

            nargs = getattr(opt, "nargs", None)
            if nargs is not None:
                kwargs["nargs"] = nargs

            if opt_type is bool:
                # Boolean flags: --flag / --no-flag (if allowed), else store_true
                if self._allow_boolean_negation:
                    kwargs["action"] = BooleanOptionalAction
                else:
                    kwargs["action"] = "store_true"
            else:
                # Normal typed option
                if opt_type is not None:
                    kwargs["type"] = opt_type

            self._parser.add_argument(*flags, **kwargs)

    def parse(self, args: List[str]) -> Dict[str, Any]:
        parsed, _ = self._parser.parse_known_args(args)
        return {k: v for k, v in vars(parsed).items() if v is not None}