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
