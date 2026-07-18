import json

import pytest

from aio_conf.core import ConfigSpec, OptionSpec


def test_python_types_serialize_and_round_trip():
    spec = ConfigSpec(
        [
            OptionSpec("port", int, default=8000),
            OptionSpec("debug", bool, default=False),
            OptionSpec("metadata", dict, default={}),
        ]
    )

    serialized = spec.to_json()
    assert json.loads(serialized)["options"][0]["type"] == "int"
    restored = ConfigSpec.from_dict(json.loads(serialized))
    assert [option.type for option in restored.options] == ["int", "bool", "dict"]


def test_default_validator_is_active():
    with pytest.raises(ValueError, match="Duplicate option name"):
        ConfigSpec([OptionSpec("port", int), OptionSpec("port", int)])


def test_unknown_option_fields_are_rejected():
    with pytest.raises(ValueError, match="env_var"):
        ConfigSpec.from_dict(
            {"options": [{"name": "port", "type": "int", "env_var": "PORT"}]}
        )


def test_required_option_without_value_is_rejected():
    from aio_conf import AIOConfig

    config = AIOConfig(ConfigSpec([OptionSpec("token", str, required=True)]))
    with pytest.raises(ValueError, match="Required option 'token'"):
        config.load(env={})
