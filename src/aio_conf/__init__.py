from .core import OptionSpec, ConfigSpec, AIOConfig


try:
    from .meta._version import __version__  # type: ignore  # noqa
except ImportError:
    __version__ = "0.0.0+local"


__all__ = ["OptionSpec", "ConfigSpec", "AIOConfig"]
