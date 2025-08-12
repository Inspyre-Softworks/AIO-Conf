from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import json

from aio_conf.core.opt_spec import OptionSpec


ValidatorFn = Callable[['ConfigSpec'], None]


@dataclass(slots=True)
class ConfigSpec:
    """
    Configuration specification with optional auto-validation hooks.

    Auto-validation:
        - Runs on construction (__post_init__), from_dict(), from_json_file(),
          and after mutators (add_option/remove_option/sort_options).
        - Toggle with enable_validation()/disable_validation().
        - Inject a custom validator callable with set_validator().

    Notes:
        The default validator is lazily imported from 'aio_conf.validation'
        (function name: validate_spec). If not found, validation silently
        becomes a no-op unless you inject your own.
    """

    options: list[OptionSpec] = field(default_factory=list)

    # --- validation controls (instance-scoped) ---
    _auto_validate: bool = field(default=True, repr=False, compare=False)
    _validator: Optional[ValidatorFn] = field(default=None, repr=False, compare=False)

    # ---------- Lifecycle ----------

    def __post_init__(self) -> None:
        if self._auto_validate:
            self._validate()

    # ---------- Construction / Serialization ----------

    @classmethod
    def from_json_file(cls, path: str | Path) -> 'ConfigSpec':
        """
        Load a configuration from a JSON file and auto-validate (if enabled).
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f'No such file: {p}')
        with p.open('r', encoding='utf-8') as f:
            data = json.load(f)
        inst = cls.from_dict(data)
        return inst

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ConfigSpec':
        """
        Construct a ConfigSpec from a Python dictionary and auto-validate (if enabled).
        """
        raw_options = data.get('options')
        if raw_options is None:
            raise ValueError("Missing required key: 'options'")
        if not isinstance(raw_options, list):
            raise ValueError("'options' must be a list")

        option_fields = {f.name for f in OptionSpec.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        opts: list[OptionSpec] = []
        for opt in raw_options:
            if not isinstance(opt, dict):
                raise ValueError('Each option must be a dictionary')
            filtered = {k: v for k, v in opt.items() if k in option_fields}
            opts.append(OptionSpec(**filtered))

        inst = cls(opts)
        # __post_init__ already validated, but keep this explicit if someone later disables it in __init__
        if inst._auto_validate:
            inst._validate()
        return inst

    def to_dict(self) -> dict[str, Any]:
        def opt_to_dict(o: OptionSpec) -> dict[str, Any]:
            fields = o.__dataclass_fields__.keys()  # type: ignore[attr-defined]
            return {k: getattr(o, k) for k in fields}
        return {'options': [opt_to_dict(o) for o in self.options]}

    def to_json(self, *, indent: int = 2, sort_keys: bool = True) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=sort_keys)

    def to_json_file(
        self,
        path: str | Path,
        return_path_on_success: Optional[bool] = None,
        *,
        indent: int = 2,
        sort_keys: bool = True,
    ) -> Optional[str | Path]:
        """
        Dump a ConfigSpec to disk. Tries the Developer Toolkit dumper first.
        """
        p = Path(path)
        try:
            from aio_conf.Developer_Toolkit.dumper import dump_spec  # type: ignore
            return dump_spec(self, p, return_path_on_success=bool(return_path_on_success))
        except Exception:
            pass

        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('w', encoding='utf-8') as f:
            f.write(self.to_json(indent=indent, sort_keys=sort_keys))
        return p if return_path_on_success else None

    # ---------- Mutators / Queries ----------

    def add_option(self, option: OptionSpec, *, replace: bool = True) -> None:
        if not hasattr(option, 'name'):
            raise ValueError("OptionSpec must have a 'name' field")
        existing_idx = next((i for i, o in enumerate(self.options) if getattr(o, 'name', None) == option.name), None)
        if existing_idx is not None and replace:
            self.options[existing_idx] = option
        else:
            self.options.append(option)
        if self._auto_validate:
            self._validate()

    def remove_option(self, name: str) -> bool:
        idx = next((i for i, o in enumerate(self.options) if getattr(o, 'name', None) == name), None)
        if idx is None:
            return False
        del self.options[idx]
        if self._auto_validate:
            self._validate()
        return True

    def get_option(self, name: str) -> Optional[OptionSpec]:
        return next((o for o in self.options if getattr(o, 'name', None) == name), None)

    def sort_options(self, key: str = 'name', reverse: bool = False) -> None:
        fields = OptionSpec.__dataclass_fields__.keys()  # type: ignore[attr-defined]
        if key not in fields:
            raise KeyError(f"Invalid sort key '{key}'. Must be one of: {', '.join(fields)}")
        self.options.sort(key=lambda o: getattr(o, key, None), reverse=reverse)
        if self._auto_validate:
            self._validate()

    # ---------- Validation controls ----------

    def set_validator(self, validator: Optional[ValidatorFn]) -> None:
        """
        Inject a custom validator callable or disable by passing None.
        Callable signature: (spec: ConfigSpec) -> None (raise on failure).
        """
        self._validator = validator
        if self._auto_validate and validator is not None:
            self._validate()

    def enable_validation(self) -> None:
        self._auto_validate = True
        self._validate()

    def disable_validation(self) -> None:
        self._auto_validate = False

    # ---------- Internals ----------

    def _validate(self) -> None:
        validator = self._validator or self._import_default_validator()
        if validator is not None:
            validator(self)

    @staticmethod
    def _import_default_validator() -> Optional[ValidatorFn]:
        """
        Lazy import to avoid hard dependency if validator module isn't present.
        Adjust the module path here if your validator lives elsewhere.
        """
        try:
            from aio_conf.validation import validate_spec  # type: ignore
            return validate_spec
        except Exception:
            return None


__all__ = ['ConfigSpec']
