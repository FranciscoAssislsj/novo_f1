import pandas as pd
import pytest

from novo_f1.transformation.strategy import (
    COMPOUND_COLOURS,
    compound_colour,
    pit_stop_counts,
    pit_summary,
    tyre_timeline,
)


def test_tyre_timeline(stints, drivers):
    result = tyre_timeline(stints, drivers)

    hard = result[result["compound"] == "HARD"].iloc[0]
    assert hard["lap_end"] == hard["lap_start"] == 3
    assert hard["laps"] == 1
    assert hard["colour"] == COMPOUND_COLOURS["HARD"]
    assert result["name_acronym"].tolist() == ["VER", "VER", "LEC"]


def test_tyre_timeline_missing_optional_columns(drivers):
    frame = pd.DataFrame({"driver_number": [1], "stint_number": [1], "lap_start": [1]})

    result = tyre_timeline(frame, drivers)

    assert result.loc[0, "compound"] == "UNKNOWN"
    assert result.loc[0, "laps"] == 1


def test_tyre_timeline_empty(drivers):
    assert tyre_timeline(pd.DataFrame(), drivers).empty


@pytest.mark.parametrize(
    ("compound", "expected"),
    [("soft", "#DA291C"), (None, "#8A8A8A"), ("TEST_UNKNOWN", "#8A8A8A")],
)
def test_compound_colour(compound, expected):
    assert compound_colour(compound) == expected


def test_pit_summary_prefers_lane_duration(pit, drivers):
    result = pit_summary(pit, drivers).set_index("name_acronym")

    assert "pit_duration" not in result.columns
    assert result.loc["VER", "lane_duration"] == 22.5
    assert result.loc["PER", "lane_duration"] == 30.1
    assert pd.isna(result.loc["PER", "stop_duration"])


def test_pit_summary_before_stop_duration_existed(drivers):
    frame = pd.DataFrame(
        {"driver_number": [1], "lap_number": [10], "lane_duration": [21.0]}
    )

    result = pit_summary(frame, drivers)

    assert pd.isna(result.loc[0, "stop_duration"])


def test_pit_summary_only_deprecated_field(drivers):
    frame = pd.DataFrame(
        {"driver_number": [1], "lap_number": [10], "pit_duration": [21.0]}
    )

    assert pit_summary(frame, drivers).loc[0, "lane_duration"] == 21.0


def test_pit_stop_counts(pit, drivers):
    counts = pit_stop_counts(pit_summary(pit, drivers))

    assert counts["name_acronym"].tolist() == ["VER", "PER"]
    assert counts["stops"].tolist() == [1, 1]


def test_pit_empty(drivers):
    assert pit_summary(pd.DataFrame(), drivers).empty
    assert pit_stop_counts(pd.DataFrame()).empty
