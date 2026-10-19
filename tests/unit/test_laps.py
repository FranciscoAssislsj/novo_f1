import pandas as pd
import pytest

from novo_f1.transformation.laps import (
    assign_stints,
    best_sectors,
    clean_laps,
    fastest_lap,
    fastest_lap_per_driver,
    remove_outliers,
    stint_pace,
)


@pytest.mark.parametrize(
    ("durations", "expected"),
    [([], None), ([None, None], None), ([90.0], 90.0), ([95.2, 93.8, None], 93.8)],
)
def test_fastest_lap_edge_cases(durations, expected):
    assert fastest_lap(durations) == expected


def test_clean_laps_drops_null_and_pit_out(laps):
    result = clean_laps(laps)

    assert len(result) == 4
    assert not result["is_pit_out_lap"].any()
    assert result["lap_duration"].notna().all()


def test_clean_laps_keep_pit_out(laps):
    assert len(clean_laps(laps, drop_pit_out=False)) == 5


def test_clean_laps_empty():
    assert clean_laps(pd.DataFrame()).empty


def test_remove_outliers():
    frame = pd.DataFrame(
        {"driver_number": [1, 1, 1, 1], "lap_duration": [90.0, 91.0, 90.5, 130.0]}
    )

    result = remove_outliers(frame)

    assert result["lap_duration"].tolist() == [90.0, 91.0, 90.5]


def test_fastest_lap_per_driver(laps, drivers):
    result = fastest_lap_per_driver(laps, drivers)

    assert result["name_acronym"].tolist() == ["LEC", "VER"]
    assert result["delta"].tolist() == pytest.approx([0.0, 0.5])


def test_fastest_lap_per_driver_no_valid_laps(drivers):
    frame = pd.DataFrame({"driver_number": [1], "lap_duration": [None]})

    assert fastest_lap_per_driver(frame, drivers).empty


def test_best_sectors_ideal_lap(laps, drivers):
    result = best_sectors(laps, drivers).set_index("name_acronym")

    assert result.loc["LEC", "ideal_lap"] == pytest.approx(24.8 + 39.9 + 29.8)
    assert result.loc["VER", "duration_sector_1"] == pytest.approx(25.0)


def test_best_sectors_missing_columns(drivers):
    assert best_sectors(pd.DataFrame({"driver_number": [1]}), drivers).empty


def test_assign_stints_handles_open_stint(laps, stints):
    result = assign_stints(laps, stints).set_index(["driver_number", "lap_number"])

    assert result.loc[(1, 3), "compound"] == "HARD"
    assert result.loc[(1, 3), "tyre_age"] == 3
    assert result.loc[(16, 3), "tyre_age"] == 4


def test_stint_pace(laps, stints, drivers):
    result = stint_pace(laps, stints, drivers)

    ver = result[result["name_acronym"] == "VER"].iloc[0]
    assert ver["compound"] == "MEDIUM"
    assert ver["laps"] == 1
    lec = result[result["name_acronym"] == "LEC"].iloc[0]
    assert lec["best_lap"] == pytest.approx(94.5)


def test_stint_pace_without_stints(laps, drivers):
    assert stint_pace(laps, pd.DataFrame(), drivers).empty
