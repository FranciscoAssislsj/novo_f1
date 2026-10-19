from datetime import UTC, date, datetime

import pytest

from novo_f1.utils.query import build_query, format_value


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ({"session_key": 9161}, "session_key=9161"),
        ({"speed>=": 315}, "speed>=315"),
        ({"interval>": 0, "interval<": 0.005}, "interval>0&interval<0.005"),
        ({"driver_number": [4, 81]}, "driver_number=4&driver_number=81"),
        ({"session_key": "latest"}, "session_key=latest"),
        ({"flag": "BLACK AND WHITE"}, "flag=BLACK%20AND%20WHITE"),
        (
            {"date>=": date(2023, 1, 1), "date<": "2023-09-01"},
            "date>=2023-01-01&date<2023-09-01",
        ),
        ({"csv": True}, "csv=true"),
        ({"session_key": None}, ""),
        ({}, ""),
    ],
)
def test_build_query(filters, expected):
    assert build_query(filters) == expected


def test_build_query_encodes_timezone_plus_sign():
    moment = datetime(2023, 9, 16, 13, 3, 35, 200000, tzinfo=UTC)

    query = build_query({"date>": moment})

    assert query == "date>2023-09-16T13:03:35.200000%2B00:00"


@pytest.mark.parametrize("key", ["Speed", "speed=>", "speed!", "a b", ""])
def test_build_query_rejects_invalid_keys(key):
    with pytest.raises(ValueError, match="Filtro inválido"):
        build_query({key: 1})


@pytest.mark.parametrize(
    ("value", "expected"),
    [(False, "false"), (3.5, "3.5"), (date(2024, 5, 1), "2024-05-01")],
)
def test_format_value(value, expected):
    assert format_value(value) == expected
