from datetime import UTC, datetime, timedelta

import pytest

from novo_f1.config.settings import Settings
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.services.repository import Repository
from novo_f1.storage.parquet_store import ParquetStore

NOW = datetime(2026, 10, 19, 12, tzinfo=UTC)


@pytest.fixture
def client(mocker, payloads):
    fake = mocker.Mock()
    fake.get.side_effect = lambda endpoint, filters: payloads.get(str(endpoint), [])
    return fake


@pytest.fixture
def repository(client, tmp_path):
    return Repository(
        client, ParquetStore(tmp_path), timedelta(hours=24), now=lambda: NOW
    )


def test_session_data_fetches_once_then_reads_cache(repository, client):
    first = repository.session_data(Endpoint.LAPS, 9161, 2023)
    second = repository.session_data(Endpoint.LAPS, 9161, 2023)

    assert len(first) == len(second) == 6
    client.get.assert_called_once_with("laps", {"session_key": 9161})


def test_empty_responses_are_not_cached(repository, client):
    repository.session_data(Endpoint.TEAM_RADIO, 9161, 2023)
    repository.session_data(Endpoint.TEAM_RADIO, 9161, 2023)

    assert client.get.call_count == 2


def test_race_only_endpoint_skipped_for_non_race(repository, client):
    frame = repository.session_data(Endpoint.INTERVALS, 9160, 2023, "Qualifying")

    assert frame.empty
    client.get.assert_not_called()


def test_race_only_endpoint_fetched_for_sprint(repository, client):
    frame = repository.session_data(Endpoint.INTERVALS, 9159, 2023, "Race")

    assert len(frame) == 3


def test_session_data_rejects_telemetry(repository):
    with pytest.raises(ValueError, match="lap_telemetry"):
        repository.session_data(Endpoint.CAR_DATA, 9161, 2023)


def test_past_calendar_is_immutable(repository, client, tmp_path):
    repository.meetings(2023)
    repository.meetings(2023)

    client.get.assert_called_once_with("meetings", {"year": 2023})


def test_current_year_calendar_expires(client, tmp_path):
    clock = {"now": NOW}
    repository = Repository(
        client,
        ParquetStore(tmp_path),
        timedelta(hours=24),
        now=lambda: clock["now"],
    )

    repository.sessions(2026)
    repository.sessions(2026)
    assert client.get.call_count == 1

    clock["now"] = NOW + timedelta(days=2)
    repository.sessions(2026)
    assert client.get.call_count == 2


def test_lap_telemetry_uses_window_and_caches(repository, client, tmp_path):
    window = (
        datetime(2023, 9, 17, 12, 3, tzinfo=UTC),
        datetime(2023, 9, 17, 12, 4, 35, tzinfo=UTC),
    )

    frame = repository.lap_telemetry(Endpoint.CAR_DATA, 9161, 2023, 1, 2, window)
    repository.lap_telemetry(Endpoint.CAR_DATA, 9161, 2023, 1, 2, window)

    assert len(frame) == 3
    client.get.assert_called_once_with(
        "car_data",
        {
            "session_key": 9161,
            "driver_number": 1,
            "date>=": window[0],
            "date<": window[1],
        },
    )
    expected = tmp_path / "raw" / "car_data" / "year=2023"
    assert (expected / "session_key=9161_driver=1_lap=2.parquet").is_file()


def test_lap_telemetry_rejects_other_endpoints(repository):
    window = (NOW, NOW)

    with pytest.raises(ValueError, match="telemetria"):
        repository.lap_telemetry(Endpoint.LAPS, 1, 2023, 1, 1, window)


def test_from_settings_builds_components(tmp_path):
    repository = Repository.from_settings(Settings(data_dir=tmp_path))

    assert repository.store.root == tmp_path
    assert repository.calendar_ttl == timedelta(hours=24)
    repository.client.close()
