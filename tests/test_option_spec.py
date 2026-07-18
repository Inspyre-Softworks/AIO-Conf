import pytest

from aio_conf.core import OptionSpec


@pytest.mark.parametrize(
    "value,expected",
    [
        ("a,b,c", ["a", "b", "c"]),
        ("[1, 2, 3]", [1, 2, 3]),
        ([], []),
    ],
)
def test_list_coercion(value, expected):
    opt = OptionSpec("items", "list")
    assert opt.coerce(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ('{"host": "localhost", "port": 5432}', {"host": "localhost", "port": 5432}),
        ("host=localhost,port=5432", {"host": "localhost", "port": 5432}),
    ],
)
def test_dict_coercion(value, expected):
    opt = OptionSpec("database", "dict")
    assert opt.coerce(value) == expected


@pytest.mark.parametrize("declared_type", [bool, "bool"])
def test_boolean_coercion_is_consistent_for_python_and_string_types(declared_type):
    opt = OptionSpec("debug", declared_type)
    assert opt.coerce("false") is False
    assert opt.coerce("true") is True


def test_tuple_type_preserves_tuple_shape():
    assert OptionSpec("items", tuple).coerce("a,b") == ("a", "b")


def test_invalid_boolean_string_is_rejected():
    with pytest.raises(ValueError, match="Expected a boolean"):
        OptionSpec("debug", bool).coerce("sometimes")
