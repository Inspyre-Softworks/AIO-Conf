from __future__ import annotations

from typing import Any, Iterable, List, Sequence, Union

from aio_conf.core import ConfigSpec, OptionSpec


def build_option(
    name:        str,
    type_:       Union[type, str],
    default:     Any = None,
    env:         str | None = None,
    cli:         str | list[str] | None = None,
    required:    bool = False,
    description: str | None = None,
) -> OptionSpec:
    """
    Create an OptionSpec with sane defaults and flexible type/CLI inputs.

    Parameters:
        name (str):
            Canonical option name.

        type_ (Union[type, str]):
            Python type (e.g., int, bool, str, Path) or a string type name
            recognized by OptionSpec ('int', 'bool', 'str', 'path', etc.).

        default (Optional[Any]):
            Default value if unspecified across all sources. Defaults to None.

        env (Optional[str]):
            Environment variable name. Defaults to None.

        cli (Optional[str, List[str]):
            One or more CLI flags; a string is normalized to a list. Defaults to None.

        required (Optional[bool]):
            Whether this option must be provided by some source. Defaults to False.

        description (Optional[str]):
            Human-friendly description. Defaults to OptionSpec's default.

    Returns:
        OptionSpec
    """
    return OptionSpec(
        name=name,
        type=type_,
        default=default,
        env=env,
        cli=cli,
        required=required,
        description=description or 'No description provided.',
    )


def build_config(options: Sequence[OptionSpec]) -> ConfigSpec:
    """
    Create a ConfigSpec from a sequence of OptionSpec objects.

    Parameters:
        options (Sequence[OptionSpec]):
            Iterable of already-constructed OptionSpec instances.

    Returns:
        ConfigSpec
    """
    # ConfigSpec wants a list; enforce a copy to avoid external mutation.
    return ConfigSpec(list(options))


class ConfigBuilder:
    """
    Fluent builder for ConfigSpec.

    Example:
        >>> builder = ConfigBuilder()
        >>> builder.add('log_level', 'str', default='INFO', cli=['--log-level', '-l'])
        >>> builder.add('debug', 'bool', default=False, cli='--debug')
        >>> spec = builder.build()
    """

    def __init__(self) -> None:
        self._options: list[OptionSpec] = []

    def add(
        self,
        name: str,
        type: Union[type, str],
        *,
        default: Any = None,
        env: str | None = None,
        cli: str | list[str] | None = None,
        required: bool = False,
        description: str | None = None,
    ) -> 'ConfigBuilder':
        """
        Add an option and return self for chaining.
        """
        opt = build_option(
            name=name,
            type_=type,
            default=default,
            env=env,
            cli=cli,
            required=required,
            description=description,
        )
        self._options.append(opt)
        return self

    def extend(self, options: Iterable[OptionSpec]) -> 'ConfigBuilder':
        """
        Add multiple OptionSpec objects.
        """
        self._options.extend(list(options))
        return self

    def build(self) -> ConfigSpec:
        """
        Produce a ConfigSpec with the accumulated options.
        """
        return build_config(self._options)


__all__ = [
    'build_option',
    'build_config',
    'ConfigBuilder',
]
