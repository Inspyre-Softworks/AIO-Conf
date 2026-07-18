from pathlib import Path

import pytest

from aio_conf.cli import main as cli_main
from aio_conf.core import ConfigSpec, OptionSpec


@pytest.fixture(autouse=True)
def isolate_platform_config(tmp_path, monkeypatch):
    config_dir = tmp_path / "user-config"
    monkeypatch.setattr(
        "aio_conf.spec_registry.platformdirs.user_config_path",
        lambda _app_name, _app_author: config_dir,
    )


def write_spec(path: Path) -> None:
    spec = ConfigSpec(
        [
            OptionSpec("app_name", "str", default="demo", env="APP_NAME"),
            OptionSpec("debug", "bool", default=False, env="APP_DEBUG"),
        ]
    )
    path.write_text(spec.to_json(), encoding="utf-8")


def test_cli_validate_and_sample(tmp_path, capsys):
    spec_path = tmp_path / "spec.json"
    write_spec(spec_path)

    exit_code = cli_main(["validate", str(spec_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Gold star" in captured.out

    sample_path = tmp_path / "sample.toml"
    exit_code = cli_main(["sample", str(spec_path), "--output", str(sample_path), "--format", "toml"])
    assert exit_code == 0
    assert "sample" in capsys.readouterr().out.lower()
    assert sample_path.exists()
    text = sample_path.read_text()
    assert "app_name" in text


def test_cli_init(tmp_path, capsys):
    target = tmp_path / "new-spec.json"
    exit_code = cli_main(["init", str(target)])
    assert exit_code == 0
    assert target.exists()
    out = capsys.readouterr().out
    assert "starter spec" in out


def test_cli_init_uses_platform_default_path(tmp_path, capsys, monkeypatch):
    config_dir = tmp_path / "platform-config"
    calls = []

    def fake_user_config_path(app_name, app_author):
        calls.append((app_name, app_author))
        return config_dir

    monkeypatch.setattr(
        "aio_conf.spec_registry.platformdirs.user_config_path",
        fake_user_config_path,
    )

    exit_code = cli_main(["init"])

    target = config_dir / "config_spec.json"
    assert exit_code == 0
    assert target.exists()
    assert calls
    assert set(calls) == {("aio-conf", "Inspyre Softworks")}
    assert str(target) in capsys.readouterr().out


def test_cli_list_tracks_created_and_given_specs(tmp_path, capsys):
    created = tmp_path / "created.json"
    given = tmp_path / "given.json"

    assert cli_main(["init", str(created)]) == 0
    write_spec(given)
    assert cli_main(["validate", str(given)]) == 0
    assert cli_main(["sample", str(given), "--format", "json"]) == 0
    capsys.readouterr()

    assert cli_main(["list"]) == 0
    output = capsys.readouterr().out
    assert str(created.resolve()) in output
    assert output.count(str(given.resolve())) == 1


def test_cli_list_marks_missing_specs(tmp_path, capsys):
    target = tmp_path / "temporary.json"
    assert cli_main(["init", str(target)]) == 0
    target.unlink()
    capsys.readouterr()

    assert cli_main(["list"]) == 0
    assert f"{target.resolve()} [missing]" in capsys.readouterr().out
