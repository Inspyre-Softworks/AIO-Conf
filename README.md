# AIO-Conf

A minimal configuration system that merges configuration from CLI arguments,
environment variables, config files and defaults. Configuration specs can be
defined in JSON and loaded with `AIOConfig`.

## Usage

```python
from aio_conf import AIOConfig

cfg = AIOConfig.load_from_spec('spec.json')
cfg.load(cli_args=['--port', '8000'], file_path='config.json')
print(cfg.as_dict())
```

Run tests with:

```bash
pytest -q
```
