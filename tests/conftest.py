"""Fixtures compartilhadas: payloads reduzidos da OpenF1, sem rede."""

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "openf1_payloads.json"
_PAYLOADS: dict[str, list[dict[str, Any]]] = json.loads(
    FIXTURES.read_text(encoding="utf-8")
)


@pytest.fixture
def payloads() -> dict[str, list[dict[str, Any]]]:
    """Cópia dos payloads JSON por endpoint."""
    return copy.deepcopy(_PAYLOADS)


def _frame(name: str) -> pd.DataFrame:
    return pd.DataFrame.from_records(copy.deepcopy(_PAYLOADS[name]))


@pytest.fixture
def drivers() -> pd.DataFrame:
    return _frame("drivers")


@pytest.fixture
def race_result() -> pd.DataFrame:
    return _frame("session_result_race")


@pytest.fixture
def quali_result() -> pd.DataFrame:
    return _frame("session_result_quali")


@pytest.fixture
def starting_grid() -> pd.DataFrame:
    return _frame("starting_grid")


@pytest.fixture
def laps() -> pd.DataFrame:
    return _frame("laps")


@pytest.fixture
def stints() -> pd.DataFrame:
    return _frame("stints")


@pytest.fixture
def pit() -> pd.DataFrame:
    return _frame("pit")


@pytest.fixture
def position() -> pd.DataFrame:
    return _frame("position")


@pytest.fixture
def intervals() -> pd.DataFrame:
    return _frame("intervals")


@pytest.fixture
def car_data() -> pd.DataFrame:
    return _frame("car_data")


@pytest.fixture
def location() -> pd.DataFrame:
    return _frame("location")


@pytest.fixture
def weather() -> pd.DataFrame:
    return _frame("weather")


@pytest.fixture
def race_control() -> pd.DataFrame:
    return _frame("race_control")


@pytest.fixture
def meetings() -> pd.DataFrame:
    return _frame("meetings")


@pytest.fixture
def sessions() -> pd.DataFrame:
    return _frame("sessions")


@pytest.fixture
def championship_drivers() -> pd.DataFrame:
    return _frame("championship_drivers")
