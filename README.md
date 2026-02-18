# AIO-Conf

AIO-Conf is a tiny configuration system that unifies values from multiple
sources: command-line arguments, environment variables, configuration files and
defaults.  Specifications are declared up front so each option knows how to be
parsed and coerced into the correct Python type.

## Installation

This project uses [Poetry](https://python-poetry.org/).  From the project
directory install dependencies with:

```bash
poetry install
```

## Defining a specification

You can declare options programmatically using `OptionSpec` and `ConfigSpec`:

```python
from aio_conf.core import ConfigSpec, OptionSpec

spec = ConfigSpec([
    OptionSpec("port", int, default=8000, env="APP_PORT", cli="--port"),
    OptionSpec("debug", bool, default=False, env="APP_DEBUG", cli="--debug"),
])
```

The spec can also be stored in JSON and loaded with
`ConfigSpec.from_json_file()` or via `AIOConfig.load_from_spec()`.

## Loading configuration

`AIOConfig` merges all sources with the following precedence:

1. CLI arguments
2. Environment variables (including nested values like `APP_DB__HOST`)
3. File values (`json`, `yaml`, `toml` or `ini`/`cfg`)
4. Defaults defined in the spec

```python
from aio_conf import AIOConfig

cfg = AIOConfig(spec)
cfg.load(
    cli_args=["--port", "9000"],
    env={"APP_DEBUG": "true"},
    file_path="config.json",
)
print(cfg.as_dict())
```
The `env` parameter accepts a mapping of environment variables and defaults to
`os.environ` when omitted.

Configuration can be written to an INI file:

```python
cfg.save_ini("settings.ini")
```

## Command line helper

Install the project (or use `poetry run`) to access the `aio-conf` CLI:

```bash
aio-conf init spec.json          # create a starter spec template
aio-conf validate spec.json      # sanity check the spec
aio-conf sample spec.json --format toml --output sample.toml
```

All commands provide blunt-but-helpful feedback, and `sample` understands the
same output formats that the loader accepts.

## Testing

Run the test suite with:

```bash
pytest -q
```
