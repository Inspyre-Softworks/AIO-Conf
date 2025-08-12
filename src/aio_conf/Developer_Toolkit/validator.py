from __future__ import annotations

import re
from typing import Iterable, Optional, Set

from ..core import ConfigSpec


class ConfigSpecValidator:
    """
    ConfigSpec validator with configurable rule toggles.

    Parameters:
        require_unique_names (bool):
            Enforce unique option names. Defaults to True.

        require_defaults_for_required (bool):
            Require that required options have non-None defaults. Defaults to False.

        check_default_type (bool):
            Ensure default values match declared type (using OptionSpec.coerce if available).
            Defaults to True.

        enforce_cli_flag_shape (bool):
            Ensure all CLI flags start with '-' or '--'. Defaults to True.

        require_unique_cli_flags (bool):
            Disallow duplicate CLI flags across options. Defaults to True.

        require_unique_env_names (bool):
            Disallow duplicate env var names across options. Defaults to True.

        enforce_name_pattern (Optional[str]):
            Regex pattern for option names; if provided, names must fully match.
            Example: r'^[a-z_][a-z0-9_]*$'. Defaults to None.

        enforce_env_pattern (Optional[str]):
            Regex pattern for env names; if provided, env must fully match.
            Example: r'^[A-Z][A-Z0-9_]*$'. Defaults to None.
    """

    def __init__(
        self,
        *,
        require_unique_names: bool = True,
        require_defaults_for_required: bool = False,
        check_default_type: bool = True,
        enforce_cli_flag_shape: bool = True,
        require_unique_cli_flags: bool = True,
        require_unique_env_names: bool = True,
        enforce_name_pattern: Optional[str] = None,
        enforce_env_pattern: Optional[str] = None,
    ) -> None:
        self.require_unique_names = require_unique_names
        self.require_defaults_for_required = require_defaults_for_required
        self.check_default_type = check_default_type
        self.enforce_cli_flag_shape = enforce_cli_flag_shape
        self.require_unique_cli_flags = require_unique_cli_flags
        self.require_unique_env_names = require_unique_env_names
        self.enforce_name_pattern = re.compile(enforce_name_pattern) if enforce_name_pattern else None
        self.enforce_env_pattern = re.compile(enforce_env_pattern) if enforce_env_pattern else None

    def validate(self, spec: ConfigSpec) -> None:
        """
        Validate a ConfigSpec in-place; raises ValueError on the first failure.
        """
        opts = getattr(spec, 'options', None) or []
        if self.require_unique_names:
            self._check_unique_names(opts)

        if self.require_defaults_for_required:
            self._check_required_defaults(opts)

        if self.check_default_type:
            self._check_default_types(opts)

        if self.enforce_cli_flag_shape or self.require_unique_cli_flags:
            self._check_cli_flags(opts)

        if self.require_unique_env_names or self.enforce_env_pattern is not None:
            self._check_envs(opts)

        if self.enforce_name_pattern is not None:
            self._check_name_pattern(opts)

    # ----- individual checks -----

    @staticmethod
    def _check_unique_names(options: Iterable) -> None:
        seen: Set[str] = set()
        for opt in options:
            name = getattr(opt, 'name', None)
            if not isinstance(name, str) or not name:
                raise ValueError('Option with missing or invalid name encountered.')
            if name in seen:
                raise ValueError(f"Duplicate option name: '{name}'")
            seen.add(name)

    @staticmethod
    def _check_required_defaults(options: Iterable) -> None:
        for opt in options:
            required = bool(getattr(opt, 'required', False))
            default = getattr(opt, 'default', None)
            name = getattr(opt, 'name', '<unknown>')
            if required and default is None:
                raise ValueError(f"Required option '{name}' has no default")

    @staticmethod
    def _coerce_if_possible(opt, value):
        # If OptionSpec has a 'coerce' method, prefer it
        coerce = getattr(opt, 'coerce', None)
        if callable(coerce):
            return coerce(value)
        # Otherwise, try a simple type call if 'type' is a real Python type
        t = getattr(opt, 'type', None)
        if isinstance(t, type):
            return t(value)
        return value

    def _check_default_types(self, options: Iterable) -> None:
        for opt in options:
            name = getattr(opt, 'name', '<unknown>')
            if not hasattr(opt, 'type'):
                continue  # nothing we can assert
            default = getattr(opt, 'default', None)
            if default is None:
                continue
            try:
                _ = self._coerce_if_possible(opt, default)
            except Exception as exc:
                raise ValueError(
                    f"Default for option '{name}' is incompatible with declared type: {exc}"
                ) from exc

    def _check_cli_flags(self, options: Iterable) -> None:
        seen: Set[str] = set()
        for opt in options:
            name = getattr(opt, 'name', '<unknown>')
            flags = getattr(opt, 'cli', None)
            if not flags:
                continue
            if isinstance(flags, str):
                flags = [flags]
            if not isinstance(flags, (list, tuple)):
                raise ValueError(f"Option '{name}' has invalid 'cli' (expected str|list[str]).")

            for flag in flags:
                if not isinstance(flag, str):
                    raise ValueError(f"Option '{name}' has non-string CLI flag: {flag!r}")
                if self.enforce_cli_flag_shape and not flag.startswith('-'):
                    raise ValueError(f"Option '{name}' has CLI flag without leading dash: '{flag}'")
                if self.require_unique_cli_flags:
                    if flag in seen:
                        raise ValueError(f"Duplicate CLI flag detected: '{flag}' (from option '{name}')")
                    seen.add(flag)

    def _check_envs(self, options: Iterable) -> None:
        seen: Set[str] = set()
        for opt in options:
            name = getattr(opt, 'name', '<unknown>')
            env = getattr(opt, 'env', None)
            if not env:
                continue
            if not isinstance(env, str):
                raise ValueError(f"Option '{name}' has non-string env name: {env!r}")
            if self.enforce_env_pattern and not self.enforce_env_pattern.fullmatch(env):
                raise ValueError(f"Option '{name}' has invalid env name '{env}' (pattern failed).")
            if self.require_unique_env_names:
                if env in seen:
                    raise ValueError(f"Duplicate env var detected: '{env}' (from option '{name}')")
                seen.add(env)

    def _check_name_pattern(self, options: Iterable) -> None:
        assert self.enforce_name_pattern is not None
        for opt in options:
            name = getattr(opt, 'name', None)
            if not isinstance(name, str) or not self.enforce_name_pattern.fullmatch(name):
                raise ValueError(f"Option name '{name}' violates enforced name pattern.")


def validate_spec(spec: ConfigSpec) -> None:
    """
    Default validation: unique names, default/typing sanity, CLI/env hygiene.
    Raises ValueError on first error.
    """
    ConfigSpecValidator(
        require_unique_names=True,
        require_defaults_for_required=False,   # flip to True if you want strictness
        check_default_type=True,
        enforce_cli_flag_shape=True,
        require_unique_cli_flags=True,
        require_unique_env_names=True,
        # Common sensible defaults you can enable if desired:
        # enforce_name_pattern=r'^[a-z_][a-z0-9_]*$',
        # enforce_env_pattern=r'^[A-Z][A-Z0-9_]*$',
    ).validate(spec)
