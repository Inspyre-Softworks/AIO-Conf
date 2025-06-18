# AIO-Conf

`aio_conf` provides a simple but flexible way to describe an application's
configuration and load values from multiple sources.  Values are resolved in the
following order of priority:

1. Command line arguments
2. Environment variables
3. Configuration files (`.json`, `.yaml` or `.ini`)
4. Defaults defined in your spec

## Developer workflow

Define a configuration spec using :class:`ConfigSpec` and :class:`OptionSpec` and
store it for distribution::

```python
from aio_conf import ConfigSpec, OptionSpec, DeveloperToolkit

spec = ConfigSpec(
    options={
        "debug": OptionSpec(name="debug", type=bool, default=False,
                             env_var="DEBUG", cli_arg="--debug"),
    },
    subconfigs={
        "database": ConfigSpec(
            options={
                "host": OptionSpec("host", str, "localhost",
                                    env_var="DB_HOST", cli_arg="--db-host"),
                "port": OptionSpec("port", int, 3306,
                                    env_var="DB_PORT", cli_arg="--db-port"),
            }
        )
    }
)

DeveloperToolkit.spec_to_json(spec, "config_spec.json")
```

The resulting `config_spec.json` can be shipped with your application.

## User workflow

Load the spec and construct :class:`AIOConfig` to obtain the merged
configuration.  The merged result can optionally be saved to an INI file for
user editing::

```python
from aio_conf import AIOConfig, DeveloperToolkit

spec = DeveloperToolkit.spec_from_json("config_spec.json")
cfg = AIOConfig(spec)

print(cfg.as_dict())

cfg.save_ini("settings.ini")
```

See the tests for more examples of the supported behaviours.
