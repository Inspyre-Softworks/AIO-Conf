from pathlib import Path

from aio_conf.cli import main as cli_main
from aio_conf.core import ConfigSpec, OptionSpec


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
