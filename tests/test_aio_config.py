import json
import os
import configparser

import pytest

from aio_conf import OptionSpec, ConfigSpec, AIOConfig
from aio_conf.developer_toolkit import DeveloperToolkit


def build_spec():
    return ConfigSpec(
        options={
            "debug": OptionSpec(name="debug", type=bool, default=False, env_var="DEBUG", cli_arg="--debug"),
        },
        subconfigs={
            "database": ConfigSpec(
                options={
                    "host": OptionSpec(name="host", type=str, default="localhost", env_var="DB_HOST", cli_arg="--db-host"),
                    "port": OptionSpec(name="port", type=int, default=3306, env_var="DB_PORT", cli_arg="--db-port"),
                }
            )
        }
    )


def test_defaults_only():
    spec = build_spec()
    cfg = AIOConfig(spec, cli_args=[], env={}, config_files=[])
    data = cfg.as_dict()
    assert data["debug"] is False
    assert data["database"]["port"] == 3306


def test_env_override(monkeypatch):
    spec = build_spec()
    monkeypatch.setenv("DB_HOST", "envhost")
    cfg = AIOConfig(spec, cli_args=[], config_files=[])
    assert cfg.as_dict()["database"]["host"] == "envhost"


def test_config_file_override(tmp_path):
    spec = build_spec()
    config_path = tmp_path / "conf.json"
    with open(config_path, "w") as f:
        json.dump({"database": {"host": "filehost"}}, f)
    cfg = AIOConfig(spec, cli_args=[], config_files=[config_path])
    assert cfg.as_dict()["database"]["host"] == "filehost"


def test_cli_override():
    spec = build_spec()
    cfg = AIOConfig(spec, cli_args=["--db-host", "clihost"], env={}, config_files=[])
    assert cfg.as_dict()["database"]["host"] == "clihost"


def test_merge_priority(monkeypatch, tmp_path):
    spec = build_spec()
    config_path = tmp_path / "conf.json"
    with open(config_path, "w") as f:
        json.dump({"database": {"host": "filehost"}}, f)
    monkeypatch.setenv("DB_HOST", "envhost")
    cfg = AIOConfig(spec, cli_args=["--db-host", "clihost"], config_files=[config_path])
    assert cfg.as_dict()["database"]["host"] == "clihost"


def test_ini_export(tmp_path):
    spec = build_spec()
    cfg = AIOConfig(spec, cli_args=["--db-port", "1234"])
    ini_path = tmp_path / "out.ini"
    cfg.save_ini(ini_path)
    cp = configparser.ConfigParser()
    cp.read(ini_path)
    assert cp["database"]["port"] == "1234"


def test_roundtrip(tmp_path):
    spec = build_spec()
    cfg = AIOConfig(spec, cli_args=["--db-port", "1234", "--db-host", "rt"])
    ini_path = tmp_path / "out.ini"
    cfg.save_ini(ini_path)
    cfg2 = AIOConfig(spec, config_files=[ini_path])
    assert cfg2.as_dict() == cfg.as_dict()


def test_spec_json(tmp_path):
    spec = build_spec()
    path = tmp_path / "spec.json"
    DeveloperToolkit.spec_to_json(spec, path)
    spec2 = DeveloperToolkit.spec_from_json(path)
    assert spec2.to_dict() == spec.to_dict()
