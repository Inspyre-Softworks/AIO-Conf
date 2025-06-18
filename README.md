# AIO-Conf

AIO-Conf provides a simple configuration object that merges settings from
multiple sources in priority order:

1. Command line arguments
2. Application configuration file
3. Environment variables
4. Default values

Configuration is defined using `OptionSpec` and `ConfigSpec`.  A spec can
contain sub-specs for subcommands, allowing an application to manage
configuration for independent routines.

Use `AIOConfig` to load the configuration:

```python
from aio_conf import OptionSpec, ConfigSpec, AIOConfig

spec = ConfigSpec(
    options=[
        OptionSpec("host", default="localhost", env="APP_HOST", cli="--host"),
        OptionSpec("port", default=8080, env="APP_PORT", cli="--port"),
    ],
)

cfg = AIOConfig(spec, config_file="config.json")
print(cfg.host, cfg.port)
```
