from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from novo_f1 import main as cli
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.services.repository import Repository
from novo_f1.services.sync import finished_sessions, sync_season
from novo_f1.storage.parquet_store import ParquetStore

NOW = datetime(2026, 10, 19, tzinfo=UTC)


@pytest.fixture
def repository(mocker, payloads, tmp_path):
    payloads["session_result"] = payloads["session_result_race"]
    client = mocker.Mock()
    client.get.side_effect = lambda endpoint, filters: payloads.get(str(endpoint), [])
    return Repository(client, ParquetStore(tmp_path), timedelta(hours=24), lambda: NOW)


def test_finished_sessions_excludes_future_and_cancelled(sessions):
    result = finished_sessions(sessions, NOW)

    assert result["session_key"].tolist() == [9161, 9160]


def test_finished_sessions_empty():
    assert finished_sessions(pd.DataFrame(), NOW).empty


def test_sync_season_loads_session_endpoints(repository):
    report = sync_season(repository, 2023, now=NOW)

    assert report.sessions == [9161, 9160]
    assert report.errors == []
    assert report.rows[Endpoint.LAPS] == 12
    starting_grid_calls = [
        call.args[1]["session_key"]
        for call in repository.client.get.call_args_list
        if call.args[0] == Endpoint.STARTING_GRID
    ]
    assert starting_grid_calls == [9160]
    endpoints = {call.args[0] for call in repository.client.get.call_args_list}
    assert Endpoint.CAR_DATA not in endpoints


def test_sync_second_run_uses_cache(repository):
    sync_season(repository, 2023, now=NOW)
    calls = repository.client.get.call_count

    sync_season(repository, 2023, session_key=9161, now=NOW)

    # Temporada passada: calendário e dados da sessão vêm todos do Parquet.
    assert repository.client.get.call_count == calls


def test_sync_records_errors_and_continues(repository):
    original = repository.client.get.side_effect

    def flaky(endpoint, filters):
        if endpoint == Endpoint.PIT:
            raise RuntimeError("boom")
        return original(endpoint, filters)

    repository.client.get.side_effect = flaky

    report = sync_season(repository, 2023, session_key=9161, now=NOW)

    assert report.sessions == [9161]
    assert report.errors == ["pit/9161: boom"]


def test_cli_parser_requires_command():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_cli_sync_prints_report(mocker, repository, capsys):
    mocker.patch.object(cli.Repository, "from_settings", return_value=repository)
    mocker.patch.object(
        cli,
        "sync_season",
        wraps=lambda repo, year, key: sync_season(repo, year, key, NOW),
    )

    code = cli.main(["sync", "--year", "2023", "--session-key", "9161"])

    assert code == 0
    assert "Sessões sincronizadas: 1" in capsys.readouterr().out


def test_cli_dashboard_runs_streamlit(mocker):
    call = mocker.patch.object(cli.subprocess, "call", return_value=0)

    assert cli.main(["dashboard"]) == 0
    command = call.call_args.args[0]
    assert command[1:4] == ["-m", "streamlit", "run"]
    assert command[4].endswith("app.py")
