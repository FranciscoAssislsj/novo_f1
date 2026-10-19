from datetime import UTC, datetime

import pytest

from novo_f1.ingestion import endpoints
from novo_f1.ingestion.endpoints import Endpoint

SESSION_FETCHERS = [
    (endpoints.fetch_drivers, Endpoint.DRIVERS),
    (endpoints.fetch_session_result, Endpoint.SESSION_RESULT),
    (endpoints.fetch_starting_grid, Endpoint.STARTING_GRID),
    (endpoints.fetch_laps, Endpoint.LAPS),
    (endpoints.fetch_stints, Endpoint.STINTS),
    (endpoints.fetch_pit, Endpoint.PIT),
    (endpoints.fetch_position, Endpoint.POSITION),
    (endpoints.fetch_intervals, Endpoint.INTERVALS),
    (endpoints.fetch_overtakes, Endpoint.OVERTAKES),
    (endpoints.fetch_championship_drivers, Endpoint.CHAMPIONSHIP_DRIVERS),
    (endpoints.fetch_championship_teams, Endpoint.CHAMPIONSHIP_TEAMS),
    (endpoints.fetch_race_control, Endpoint.RACE_CONTROL),
    (endpoints.fetch_weather, Endpoint.WEATHER),
    (endpoints.fetch_team_radio, Endpoint.TEAM_RADIO),
]


@pytest.fixture
def client(mocker):
    fake = mocker.Mock()
    fake.get.return_value = [{"ok": True}]
    return fake


def test_all_eighteen_endpoints_are_declared():
    assert len(Endpoint) == 18


@pytest.mark.parametrize(("fetcher", "endpoint"), SESSION_FETCHERS)
def test_session_fetchers(client, fetcher, endpoint):
    assert fetcher(client, 9161) == [{"ok": True}]
    client.get.assert_called_once_with(endpoint, {"session_key": 9161})


@pytest.mark.parametrize(
    ("fetcher", "endpoint"),
    [
        (endpoints.fetch_meetings, Endpoint.MEETINGS),
        (endpoints.fetch_sessions, Endpoint.SESSIONS),
    ],
)
def test_year_fetchers(client, fetcher, endpoint):
    fetcher(client, 2024)

    client.get.assert_called_once_with(endpoint, {"year": 2024})


@pytest.mark.parametrize(
    ("fetcher", "endpoint"),
    [
        (endpoints.fetch_car_data, Endpoint.CAR_DATA),
        (endpoints.fetch_location, Endpoint.LOCATION),
    ],
)
def test_telemetry_fetchers_use_time_window(client, fetcher, endpoint):
    start = datetime(2023, 9, 16, 13, 3, tzinfo=UTC)
    end = datetime(2023, 9, 16, 13, 5, tzinfo=UTC)

    fetcher(client, 9161, 81, start, end)

    client.get.assert_called_once_with(
        endpoint,
        {"session_key": 9161, "driver_number": 81, "date>=": start, "date<": end},
    )


def test_fetch_telemetry_rejects_other_endpoints(client):
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="telemetria"):
        endpoints.fetch_telemetry(client, Endpoint.LAPS, 1, 1, now, now)


@pytest.mark.parametrize(
    ("session_type", "expected"),
    [("Race", True), ("race ", True), ("Qualifying", False), (None, False)],
)
def test_is_race_session(session_type, expected):
    assert endpoints.is_race_session(session_type) is expected


def test_race_only_endpoints():
    assert {
        Endpoint.INTERVALS,
        Endpoint.OVERTAKES,
        Endpoint.CHAMPIONSHIP_DRIVERS,
        Endpoint.CHAMPIONSHIP_TEAMS,
    } == endpoints.RACE_ONLY_ENDPOINTS
