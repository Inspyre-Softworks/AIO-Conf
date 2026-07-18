import json

import pytest

from aio_conf import AIOConfig
from aio_conf.core import ConfigSpec, OptionSpec
from aio_conf.loader import load_file, parse_env
from aio_conf.writer import to_ini


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


def test_absent_boolean_flag_does_not_override_environment():
    cfg = AIOConfig(make_spec())
    cfg.load(cli_args=[], env={"APP_DEBUG": "true"})
    assert cfg.as_dict()["debug"] is True


def test_boolean_cli_supports_explicit_negation():
    cfg = AIOConfig(make_spec())
    cfg.load(cli_args=["--no-debug"], env={"APP_DEBUG": "true"})
    assert cfg.as_dict()["debug"] is False


def test_explicit_empty_environment_does_not_read_process_environment(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9001")
    cfg = AIOConfig(make_spec())
    cfg.load(env={})
    assert cfg.as_dict()["port"] == 8000


def test_file_values_are_coerced_to_the_declared_type(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"port": "9001", "debug": "false"}', encoding="utf-8")
    cfg = AIOConfig(make_spec())
    cfg.load(env={}, file_path=path)
    assert cfg.as_dict() == {"port": 9001, "debug": False}


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


def test_ini_nested_values_round_trip(tmp_path):
    data = {"DebugMode": False, "database": {"HostName": "localhost", "ports": [5432, 5433]}}
    path = tmp_path / "config.ini"
    path.write_text(to_ini(data), encoding="utf-8")
    assert load_file(path) == data


def test_loader_rejects_non_mapping_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="top level"):
        load_file(path)


def test_mutable_defaults_are_isolated_between_configs():
    spec = ConfigSpec([OptionSpec("features", list, default=[])])
    first = AIOConfig(spec)
    second = AIOConfig(spec)
    first.values["features"].append("alpha")
    assert second.values["features"] == []


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


def test_nested_env_requires_a_dictionary_option():
    spec = ConfigSpec([OptionSpec("host", "str", env="APP_HOST")])
    with pytest.raises(ValueError, match="not a dictionary"):
        parse_env(spec, {"APP_HOST__NAME": "localhost"})


def test_conflicting_nested_env_keys_are_rejected():
    spec = ConfigSpec([OptionSpec("database", "dict", env="APP_DB")])
    with pytest.raises(ValueError, match="Conflicting nested"):
        parse_env(
            spec,
            {
                "APP_DB__HOST": "localhost",
                "APP_DB__HOST__PORT": "5432",
            },
        )
