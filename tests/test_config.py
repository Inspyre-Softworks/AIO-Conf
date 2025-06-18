import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from pathlib import Path
import os
from aio_conf import OptionSpec, ConfigSpec, AIOConfig


def test_priority(tmp_path, monkeypatch):
    conf_file = tmp_path / "conf.json"
    conf_file.write_text('{"value": "file"}')

    spec = ConfigSpec([OptionSpec("value", default="default", env="TEST_VALUE", cli="--value")])

    # env overrides default
    monkeypatch.setenv("TEST_VALUE", "env")
    cfg = AIOConfig(spec, config_file=conf_file, argv=[])
    assert cfg.value == "env"

    # file overrides default when env unset
    monkeypatch.delenv("TEST_VALUE", raising=False)
    cfg = AIOConfig(spec, config_file=conf_file, argv=[])
    assert cfg.value == "file"

    # command line overrides everything
    cfg = AIOConfig(spec, config_file=conf_file, argv=["--value", "cli"])
    assert cfg.value == "cli"


def test_subcommand(tmp_path):
    conf_file = tmp_path / "conf.json"
    conf_file.write_text('{"sub": {"opt": "from_file"}}')

    sub_spec = ConfigSpec([OptionSpec("opt", default="default")])
    main_spec = ConfigSpec(options=[], subcommands={"sub": sub_spec})

    cfg = AIOConfig(main_spec, config_file=conf_file)
    subcfg = cfg.for_subcommand("sub")
    assert subcfg.opt == "from_file"
