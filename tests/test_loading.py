from aio_conf import AIOConfig
from aio_conf.core import ConfigSpec, OptionSpec


def make_spec():
    return ConfigSpec(
        [
            OptionSpec("port", int, default=8000, env="APP_PORT", cli="--port"),
            OptionSpec("debug", bool, default=False, env="APP_DEBUG", cli="--debug"),
        ]
    )


def test_precedence(tmp_path, monkeypatch):
    spec = make_spec()
    cfg = AIOConfig(spec)
    # file has port 9000
    path = tmp_path / "config.json"
    path.write_text('{"port": 9000}')
    # env has port 8001
    monkeypatch.setenv("APP_PORT", "8001")
    # CLI overrides to 8002
    cfg.load(cli_args=["--port", "8002"], file_path=str(path))
    assert cfg.as_dict()["port"] == 8002


def test_to_ini(tmp_path):
    spec = make_spec()
    cfg = AIOConfig(spec)
    cfg.load()
    ini_path = tmp_path / "out.ini"
    cfg.save_ini(ini_path)
    text = ini_path.read_text()
    assert "port = 8000" in text
