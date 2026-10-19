import pandas as pd
import pytest

from novo_f1.transformation.positions import (
    gaps_series,
    laps_down,
    position_by_lap,
    position_changes,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("+1 LAP", 1), ("+3 LAPS", 3), (1.2, 0), (None, 0), ("abc", 0)],
)
def test_laps_down(value, expected):
    assert laps_down(value) == expected


def test_position_changes(position, drivers):
    result = position_changes(position, drivers)

    assert str(result["date"].dt.tz) == "UTC"
    assert result["name_acronym"].tolist()[:2] == ["VER", "LEC"]


def test_position_by_lap(position, laps):
    result = position_by_lap(position, laps)
    table = result.pivot(index="lap_number", columns="driver_number", values="position")

    assert table.loc[0, 1] == 1
    assert table.loc[2, 1] == 1
    assert table.loc[3, 1] == 2
    assert table.loc[3, 16] == 1


def test_position_by_lap_missing_data(position):
    assert position_by_lap(position, pd.DataFrame()).empty


def test_gaps_series(intervals, drivers):
    result = gaps_series(intervals, drivers).set_index("name_acronym")

    assert result.loc["LEC", "gap_to_leader"] == 0.0
    assert result.loc["VER", "interval"] == pytest.approx(1.234)
    assert pd.isna(result.loc["PER", "gap_to_leader"])
    assert result.loc["PER", "laps_down"] == 1


def test_gaps_series_empty(drivers):
    assert gaps_series(pd.DataFrame(), drivers).empty


def test_gaps_series_null_gap_with_interval_is_not_leader(drivers):
    intervals = pd.DataFrame(
        {
            "driver_number": [1, 16],
            "date": ["2023-09-17T12:05:00+00:00", "2023-09-17T12:05:01+00:00"],
            "gap_to_leader": [None, None],
            "interval": [None, 0.582],
        }
    )

    result = gaps_series(intervals, drivers).set_index("name_acronym")

    assert result.loc["VER", "gap_to_leader"] == 0.0
    assert pd.isna(result.loc["LEC", "gap_to_leader"])
    assert result.loc["LEC", "interval"] == pytest.approx(0.582)
