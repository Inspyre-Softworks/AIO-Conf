import json

from aio_conf import AIOConfig
from aio_conf.core import ConfigSpec, OptionSpec
from aio_conf.loader import load_file, parse_env


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


def test_load_multiple_formats(tmp_path):
    data = {"port": 9001, "debug": True}
    json_path = tmp_path / "config.json"
    yaml_path = tmp_path / "config.yaml"
    toml_path = tmp_path / "config.toml"
    ini_path = tmp_path / "config.ini"

    json_path.write_text(json.dumps(data), encoding="utf-8")
    yaml_path.write_text("port: 9001\ndebug: true\n", encoding="utf-8")
    toml_path.write_text("port = 9001\ndebug = true\n", encoding="utf-8")
    ini_path.write_text("[DEFAULT]\nport = 9001\ndebug = true\n", encoding="utf-8")

    for path in [json_path, yaml_path, toml_path, ini_path]:
        loaded = load_file(path)
        assert loaded["port"] == 9001
        assert loaded["debug"] is True


def test_parse_env_with_nested_structure():
    spec = ConfigSpec(
        [
            OptionSpec("database", "dict", default={}, env="APP_DB"),
            OptionSpec("features", "list", default=[], env="APP_FEATURES"),
        ]
    )
    env = {
        "APP_DB__HOST": "localhost",
        "APP_DB__PORT": "5432",
        "APP_FEATURES": "alpha,beta,gamma",
    }
    parsed = parse_env(spec, env)
    assert parsed["database"] == {"host": "localhost", "port": 5432}
    assert parsed["features"] == ["alpha", "beta", "gamma"]
