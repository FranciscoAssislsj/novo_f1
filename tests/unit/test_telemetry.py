import pandas as pd
import pytest

from novo_f1.transformation.telemetry import (
    DRS_ELIGIBLE,
    DRS_OFF,
    DRS_ON,
    DRS_UNKNOWN,
    decode_drs,
    lap_window,
    merge_car_location,
    prepare_car_data,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, DRS_OFF),
        (1, DRS_OFF),
        (8, DRS_ELIGIBLE),
        (10, DRS_ON),
        (12, DRS_ON),
        (14, DRS_ON),
        (2, DRS_UNKNOWN),
        (3, DRS_UNKNOWN),
        (9, DRS_UNKNOWN),
        (None, DRS_UNKNOWN),
        (float("nan"), DRS_UNKNOWN),
    ],
)
def test_decode_drs(value, expected):
    assert decode_drs(value) == expected


def test_lap_window_uses_next_lap_start(laps):
    start, end = lap_window(laps, 16, 2)

    assert start == pd.Timestamp("2023-09-17T12:03:04Z")
    assert end == pd.Timestamp("2023-09-17T12:04:38.5Z")


def test_lap_window_last_lap_uses_duration(laps):
    start, end = lap_window(laps, 16, 3)

    assert end - start == pd.Timedelta(seconds=94.8 + 1)


def test_lap_window_without_duration_uses_fallback():
    laps = pd.DataFrame(
        {
            "driver_number": [1],
            "lap_number": [5],
            "date_start": ["2024-01-01T00:00:00Z"],
            "lap_duration": [None],
        }
    )

    start, end = lap_window(laps, 1, 5)

    assert end - start == pd.Timedelta(minutes=3)


@pytest.mark.parametrize(("driver", "lap"), [(1, 1), (1, 99), (44, 1)])
def test_lap_window_unavailable(laps, driver, lap):
    assert lap_window(laps, driver, lap) is None


def test_lap_window_missing_columns():
    assert lap_window(pd.DataFrame(), 1, 1) is None


def test_prepare_car_data_sorts_and_integrates_distance(car_data):
    result = prepare_car_data(car_data)

    assert result["speed"].tolist() == [72, 108, 144]
    assert result["elapsed_s"].tolist() == [0.0, 0.5, 1.0]
    assert result["distance_m"].tolist() == pytest.approx([0.0, 15.0, 35.0])
    assert result["drs_state"].tolist() == [DRS_OFF, DRS_ON, DRS_UNKNOWN]


def test_prepare_car_data_empty():
    assert prepare_car_data(pd.DataFrame()).empty


def test_merge_car_location(car_data, location):
    result = merge_car_location(prepare_car_data(car_data), location)

    assert result["x"].tolist()[:2] == [10, 15]
    assert result["y"].tolist()[:2] == [20, 25]


def test_merge_car_location_without_location(car_data):
    result = merge_car_location(prepare_car_data(car_data), pd.DataFrame())

    assert result["x"].isna().all()
