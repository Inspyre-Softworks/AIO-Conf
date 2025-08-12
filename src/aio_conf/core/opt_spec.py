from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union


@dataclass(slots=True)
class OptionSpec:
    """
    Describe a single configuration option.

    Parameters:
        name (str):
            The canonical option name (used as the key in resolved config).

        type (type | str):
            The expected Python type, or a string typename ('int', 'float', 'bool',
            'str', 'path'). May also be any callable that converts a single value.

        default (Any, optional):
            Default value used if the option is not provided by any source. Defaults to None.

        env (Optional[str], optional):
            Environment variable name associated with this option. Defaults to None.

        cli (Union[str, list[str], None], optional):
            One or more CLI flags for this option (e.g., '--log-level', '-l'). If a single
            string is given, it is normalized to a one-element list. Defaults to None.

        required (bool, optional):
            Whether the option is required (validation layer can enforce this). Defaults to False.

        description (str, optional):
            Human-readable description for help/UX. Defaults to 'No description provided.'.

    Properties:
        name (str):
            Canonical name.

        type (Union[type, str, Callable[Any]):
            Converter/type indicator.

        default (Any):
            Default value.

        env (Optional[str]):
            Environment variable name.

        cli (Optional[list[str]]):
            CLI flags (normalized to a list if provided).

        required (bool):
            Required flag.

        description (str):
            Human description.

    Methods:
        coerce(value):
            Convert an arbitrary value to the declared `type`, including support for
            common string representations (e.g., booleans, paths).

    Raises:
        TypeError:
            If `cli` is not a str/list/None.

        ValueError:
            If `type` is a string that is not recognized by the built-in mapping.

    Example Usage:
        >>> opt = OptionSpec(
        ...     name='log_level',
        ...     type='str',
        ...     default='INFO',
        ...     env='APP_LOG_LEVEL',
        ...     cli=['--log-level', '-l'],
        ... )
        >>> opt.coerce('debug')
        'debug'
    """

    # Public fields (keep 'type' to remain compatible with existing code)
    name: str
    type: Union[type, str, Callable[[Any], Any]]
    default: Any = None
    env: Optional[str] = None
    cli: Optional[list[str]] = field(default=None)
    required: bool = False
    description: str = 'No description provided.'

    # ---------- Lifecycle ----------

    def __post_init__(self) -> None:
        # Normalize cli to a list[str] if provided
        if isinstance(self.cli, str):
            self.cli = [self.cli]
        elif self.cli is not None:
            if not isinstance(self.cli, list) or not all(isinstance(x, str) for x in self.cli):
                raise TypeError('cli must be a str, a list[str], or None')

        # Validate string type names early so errors are caught at construction
        if isinstance(self.type, str):
            _ = self._resolve_type_name(self.type)  # raises if unknown

    # ---------- Coercion ----------

    def coerce(self, value: Any) -> Any:
        """
        Convert `value` into the declared `type`.

        Rules:
            - If `type` is a callable, it is called directly.
            - If `type` is a Python type (e.g., int, bool, Path), it is invoked.
            - If `type` is a string, a built-in mapping is used.
            - Booleans accept common string forms: '1','0','true','false','yes','no','on','off'.

        Parameters:
            value (Any):
                Input value to convert.

        Returns:
            Any:
                Converted value.

        Raises:
            ValueError:
                If conversion fails or an unknown string typename is used.
        """
        converter = self._get_converter()
        try:
            return converter(value)
        except Exception as exc:
            raise ValueError(
                f"Failed to coerce option '{self.name}' to {self.type!r}: {exc}"
            ) from exc

    # ---------- Internals ----------

    def _get_converter(self) -> Callable[[Any], Any]:
        if callable(self.type) and not isinstance(self.type, str):
            return self.type  # user-supplied callable or a Python type

        if isinstance(self.type, str):
            resolved = self._resolve_type_name(self.type)
            return resolved

        # Python built-in types like int/float/bool/Path
        if self.type is bool:
            return _coerce_bool
        if self.type is Path:
            return _coerce_path
        return self.type  # int, float, str, etc.

    @staticmethod
    def _resolve_type_name(name: str) -> Callable[[Any], Any]:
        table: dict[str, Callable[[Any], Any]] = {
            'str': str,
            'int': int,
            'float': float,
            'bool': _coerce_bool,
            'path': _coerce_path,
            'Path': _coerce_path,
        }
        try:
            return table[name]
        except KeyError as exc:
            raise ValueError(f"Unknown type string '{name}'. Expected one of: {', '.join(table)}") from exc


# ---------- Helper Converters ----------

def _coerce_bool(value: Any) -> bool:
    # Fast-path for actual booleans
    if isinstance(value, bool):
        return value

    # Accept integers cleanly
    if isinstance(value, int):
        return value != 0

    # Strings: flexible truthiness
    if isinstance(value, str):
        val = value.strip().lower()
        if val in {'1', 'true', 't', 'yes', 'y', 'on'}:
            return True
        if val in {'0', 'false', 'f', 'no', 'n', 'off'}:
            return False

    # Fallback to Python truthiness
    return bool(value)


def _coerce_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value
    return Path(str(value))


__all__ = ['OptionSpec']
