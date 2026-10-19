import plotly.graph_objects as go
import pytest

from novo_f1.dashboard import charts
from novo_f1.dashboard.telemetry_charts import (
    TelemetryTrace,
    telemetry_chart,
    track_map,
    weather_chart,
)
from novo_f1.transformation.calendar import season_calendar
from novo_f1.transformation.context import weather_series
from novo_f1.transformation.laps import best_sectors, clean_laps
from novo_f1.transformation.positions import gaps_series, position_by_lap
from novo_f1.transformation.results import (
    championship_standings,
    classification,
    driver_info,
    grid_vs_finish,
    with_driver_info,
)
from novo_f1.transformation.strategy import pit_summary, tyre_timeline
from novo_f1.transformation.telemetry import merge_car_location, prepare_car_data


@pytest.fixture
def styles(drivers):
    return charts.driver_styles(driver_info(drivers))


def test_driver_styles_dash_second_teammate(styles):
    assert styles[1] == ("#3671C6", "solid")
    assert styles[11] == ("#3671C6", "dash")
    assert styles[16][1] == "solid"


def test_season_timeline(meetings, sessions):
    fig = charts.season_timeline(season_calendar(meetings, sessions))

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].marker.symbol[1] == "diamond"


def test_gap_bar_skips_missing_values(race_result, drivers):
    fig = charts.gap_bar(classification(race_result, drivers), "gap_seconds", "Gap")

    assert fig.data[0].type == "bar"
    assert list(fig.data[0].y) == ["LEC", "VER"]


def test_grid_vs_finish_chart(starting_grid, race_result, drivers):
    fig = charts.grid_vs_finish_chart(
        grid_vs_finish(starting_grid, race_result, drivers)
    )

    assert len(fig.data) == 2


def test_championship_chart(championship_drivers, drivers):
    standings = championship_standings(championship_drivers, drivers)

    fig = charts.championship_chart(standings, "name_acronym", "Pilotos")

    assert list(fig.data[0].x) == [392, 124]


def test_lap_times_chart_one_trace_per_driver(laps, drivers, styles):
    fig = charts.lap_times_chart(with_driver_info(clean_laps(laps), drivers), styles)

    assert len(fig.data) == 2
    assert all(trace.type == "scatter" for trace in fig.data)
    assert fig.data[0].line.width == charts.LINE_WIDTH


def test_sector_chart(laps, drivers):
    fig = charts.sector_chart(best_sectors(laps, drivers))

    assert len(fig.data) == 3


def test_stint_gantt_one_trace_per_compound(stints, drivers):
    fig = charts.stint_gantt(tyre_timeline(stints, drivers))

    assert {trace.name for trace in fig.data} == {"Medium", "Hard", "Soft"}
    assert fig.layout.barmode == "overlay"


def test_pit_stop_chart(pit, drivers):
    fig = charts.pit_stop_chart(pit_summary(pit, drivers))

    assert len(fig.data[0].x) == 2


def test_positions_chart(position, laps, drivers, styles):
    positions = with_driver_info(position_by_lap(position, laps), drivers)

    fig = charts.positions_chart(positions, styles)

    assert len(fig.data) == 2
    assert fig.layout.yaxis.autorange == "reversed"


def test_gap_chart(intervals, drivers, styles):
    fig = charts.gap_chart(gaps_series(intervals, drivers), styles)

    assert len(fig.data) == 3
    assert fig.data[1].line.dash == "dash"


def test_telemetry_chart_panels(car_data, location):
    data = merge_car_location(prepare_car_data(car_data), location)
    traces = [
        TelemetryTrace("VER · volta 2", "#3671C6", "solid", data),
        TelemetryTrace("PER · volta 2", "#3671C6", "dash", data),
    ]

    fig = telemetry_chart(traces)

    assert len(fig.data) == 8
    assert sum(trace.showlegend for trace in fig.data) == 2


def test_track_map(car_data, location):
    data = merge_car_location(prepare_car_data(car_data), location)

    fig = track_map(data, "VER")

    assert list(fig.data[0].x) == [10, 15, 15]
    assert fig.layout.yaxis.scaleanchor == "x"


def test_weather_chart_marks_rain(weather):
    fig = weather_chart(weather_series(weather))

    assert [trace.name for trace in fig.data] == ["Ar", "Pista", "Umidade", "Chuva"]
