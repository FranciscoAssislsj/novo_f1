import numpy as np
import pandas as pd
import pytest

from novo_f1.transformation.common import as_list, normalize_colour, to_float
from novo_f1.transformation.results import (
    championship_standings,
    classification,
    driver_info,
    grid_vs_finish,
    parse_gap,
    split_duration,
)


def test_driver_info_normalises_colour_and_drops_country_code(drivers):
    info = driver_info(drivers)

    assert "country_code" not in info.columns
    assert info.set_index("driver_number").loc[1, "team_colour"] == "#3671C6"
    assert info.set_index("driver_number").loc[16, "team_colour"] == "#7F7F7F"


def test_driver_info_empty():
    assert driver_info(pd.DataFrame()).empty


def test_race_classification(race_result, drivers):
    result = classification(race_result, drivers)

    assert result["name_acronym"].tolist() == ["LEC", "VER", "PER"]
    assert result["status"].tolist() == ["Classificado", "Classificado", "DNF"]
    assert result["gap_seconds"].iloc[1] == pytest.approx(5.377)
    assert result["gap_text"].tolist() == ["", "+5.377s", "+2 LAPS"]
    assert result["best_time"].iloc[0] == pytest.approx(5400.123)


def test_quali_classification_splits_phases(quali_result, drivers):
    result = classification(quali_result, drivers).set_index("name_acronym")

    assert result.loc["VER", "q3"] == pytest.approx(90.9)
    assert result.loc["PER", "best_time"] == pytest.approx(92.8)
    assert pd.isna(result.loc["PER", "q2"])
    assert result.loc["LEC", "gap_seconds"] == pytest.approx(0.3)


def test_classification_without_duration_columns(drivers):
    frame = pd.DataFrame({"driver_number": [1], "position": [1]})

    result = classification(frame, drivers)

    assert pd.isna(result.loc[0, "best_time"])


def test_classification_empty(drivers):
    assert classification(pd.DataFrame(), drivers).empty


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, (None, "")),
        (float("nan"), (None, "")),
        (0, (0.0, "")),
        (1.5, (1.5, "+1.500s")),
        ("+1 LAP", (None, "+1 LAP")),
        ("2.25", (2.25, "+2.250s")),
        ([0.1, 0.2, None], (0.2, "+0.200s")),
        (np.array([0.4, np.nan]), (0.4, "+0.400s")),
    ],
)
def test_parse_gap(value, expected):
    assert parse_gap(value) == expected


def test_split_duration_scalar_and_array():
    assert split_duration(95.0)["best_time"] == 95.0
    phases = split_duration("[92.0, 91.0, null]")
    assert phases == {"best_time": 91.0, "q1": 92.0, "q2": 91.0, "q3": None}


def test_grid_vs_finish(starting_grid, race_result, drivers):
    result = grid_vs_finish(starting_grid, race_result, drivers).set_index(
        "name_acronym"
    )

    assert result.loc["LEC", "positions_gained"] == 1
    assert result.loc["VER", "positions_gained"] == -1
    assert pd.isna(result.loc["PER", "finish"])


def test_grid_vs_finish_missing_data(race_result, drivers):
    assert grid_vs_finish(pd.DataFrame(), race_result, drivers).empty


def test_championship_standings(championship_drivers, drivers):
    standings = championship_standings(championship_drivers, drivers)

    assert standings["name_acronym"].tolist() == ["VER", "LEC"]
    assert standings["points_gained"].tolist() == [18, 25]


def test_championship_standings_empty():
    assert championship_standings(pd.DataFrame()).empty


@pytest.mark.parametrize(
    ("value", "expected"),
    [("abc", None), (True, None), ("3", 3.0), (np.float64(2.5), 2.5), (None, None)],
)
def test_to_float(value, expected):
    assert to_float(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("[1, 2]", [1, 2]), ("[oops", None), ("{}", None), (5, None), ((1,), [1])],
)
def test_as_list(value, expected):
    assert as_list(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("e8002d", "#E8002D"),
        ("#FF8000", "#FF8000"),
        ("", "#7F7F7F"),
        ("abc", "#7F7F7F"),
    ],
)
def test_normalize_colour(value, expected):
    assert normalize_colour(value) == expected


def test_team_standings_get_team_colour(drivers):
    teams = pd.DataFrame(
        {
            "team_name": ["Red Bull Racing", "Ferrari"],
            "points_start": [500, 300],
            "points_current": [520, 325],
            "position_current": [1, 2],
        }
    )

    standings = championship_standings(teams, drivers)

    assert standings["team_colour"].tolist() == ["#3671C6", "#7F7F7F"]
