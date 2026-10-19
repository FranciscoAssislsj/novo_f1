"""Funções finas por endpoint da OpenF1."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from novo_f1.ingestion.client import OpenF1Client
from novo_f1.utils.query import FilterValue


class Endpoint(StrEnum):
    """Endpoints da OpenF1 (ver `doc_api.md`)."""

    CAR_DATA = "car_data"
    CHAMPIONSHIP_DRIVERS = "championship_drivers"
    CHAMPIONSHIP_TEAMS = "championship_teams"
    DRIVERS = "drivers"
    INTERVALS = "intervals"
    LAPS = "laps"
    LOCATION = "location"
    MEETINGS = "meetings"
    OVERTAKES = "overtakes"
    PIT = "pit"
    POSITION = "position"
    RACE_CONTROL = "race_control"
    SESSIONS = "sessions"
    SESSION_RESULT = "session_result"
    STARTING_GRID = "starting_grid"
    STINTS = "stints"
    TEAM_RADIO = "team_radio"
    WEATHER = "weather"


RACE_ONLY_ENDPOINTS = frozenset(
    {
        Endpoint.CHAMPIONSHIP_DRIVERS,
        Endpoint.CHAMPIONSHIP_TEAMS,
        Endpoint.INTERVALS,
        Endpoint.OVERTAKES,
    }
)
"""Endpoints disponíveis só em sessões do tipo corrida (Race/Sprint)."""

INCOMPLETE_ENDPOINTS = frozenset({Endpoint.OVERTAKES, Endpoint.TEAM_RADIO})
"""Endpoints cujos dados podem estar incompletos."""

BETA_ENDPOINTS = frozenset({Endpoint.CHAMPIONSHIP_DRIVERS, Endpoint.CHAMPIONSHIP_TEAMS})
"""Endpoints em beta na OpenF1."""

TELEMETRY_ENDPOINTS = frozenset({Endpoint.CAR_DATA, Endpoint.LOCATION})
"""Endpoints de alta frequência, buscados apenas sob demanda por volta."""

type Records = list[dict[str, Any]]


def is_race_session(session_type: str | None) -> bool:
    """Indica se o tipo de sessão é corrida (inclui Sprint, cujo tipo é Race)."""
    return (session_type or "").strip().lower() == "race"


def fetch(client: OpenF1Client, endpoint: str, **filters: FilterValue) -> Records:
    """Busca genérica em um endpoint com filtros de igualdade/operador."""
    return client.get(endpoint, filters)


def fetch_meetings(client: OpenF1Client, year: int) -> Records:
    """Meetings (fins de semana) de uma temporada."""
    return fetch(client, Endpoint.MEETINGS, year=year)


def fetch_sessions(client: OpenF1Client, year: int) -> Records:
    """Sessões de uma temporada."""
    return fetch(client, Endpoint.SESSIONS, year=year)


def fetch_drivers(client: OpenF1Client, session_key: int) -> Records:
    """Pilotos de uma sessão."""
    return fetch(client, Endpoint.DRIVERS, session_key=session_key)


def fetch_session_result(client: OpenF1Client, session_key: int) -> Records:
    """Resultado final de uma sessão."""
    return fetch(client, Endpoint.SESSION_RESULT, session_key=session_key)


def fetch_starting_grid(client: OpenF1Client, session_key: int) -> Records:
    """Grid de largada de uma corrida."""
    return fetch(client, Endpoint.STARTING_GRID, session_key=session_key)


def fetch_laps(client: OpenF1Client, session_key: int) -> Records:
    """Voltas de todos os pilotos de uma sessão."""
    return fetch(client, Endpoint.LAPS, session_key=session_key)


def fetch_stints(client: OpenF1Client, session_key: int) -> Records:
    """Stints e pneus de uma sessão."""
    return fetch(client, Endpoint.STINTS, session_key=session_key)


def fetch_pit(client: OpenF1Client, session_key: int) -> Records:
    """Passagens pelo pit lane de uma sessão."""
    return fetch(client, Endpoint.PIT, session_key=session_key)


def fetch_position(client: OpenF1Client, session_key: int) -> Records:
    """Mudanças de posição ao longo de uma sessão."""
    return fetch(client, Endpoint.POSITION, session_key=session_key)


def fetch_intervals(client: OpenF1Client, session_key: int) -> Records:
    """Gaps para o líder e para o carro à frente (só corridas)."""
    return fetch(client, Endpoint.INTERVALS, session_key=session_key)


def fetch_overtakes(client: OpenF1Client, session_key: int) -> Records:
    """Ultrapassagens (só corridas, pode estar incompleto)."""
    return fetch(client, Endpoint.OVERTAKES, session_key=session_key)


def fetch_championship_drivers(client: OpenF1Client, session_key: int) -> Records:
    """Campeonato de pilotos após a sessão (beta, só corridas)."""
    return fetch(client, Endpoint.CHAMPIONSHIP_DRIVERS, session_key=session_key)


def fetch_championship_teams(client: OpenF1Client, session_key: int) -> Records:
    """Campeonato de construtores após a sessão (beta, só corridas)."""
    return fetch(client, Endpoint.CHAMPIONSHIP_TEAMS, session_key=session_key)


def fetch_race_control(client: OpenF1Client, session_key: int) -> Records:
    """Mensagens da direção de prova de uma sessão."""
    return fetch(client, Endpoint.RACE_CONTROL, session_key=session_key)


def fetch_weather(client: OpenF1Client, session_key: int) -> Records:
    """Clima da sessão (amostras a cada minuto)."""
    return fetch(client, Endpoint.WEATHER, session_key=session_key)


def fetch_team_radio(client: OpenF1Client, session_key: int) -> Records:
    """Rádios da sessão (seleção parcial)."""
    return fetch(client, Endpoint.TEAM_RADIO, session_key=session_key)


def fetch_telemetry(
    client: OpenF1Client,
    endpoint: str,
    session_key: int,
    driver_number: int,
    date_start: datetime,
    date_end: datetime,
) -> Records:
    """Telemetria de alta frequência na janela ``[date_start, date_end)``.

    Raises:
        ValueError: Se o endpoint não for ``car_data`` nem ``location``.
    """
    if endpoint not in TELEMETRY_ENDPOINTS:
        raise ValueError(f"{endpoint} não é um endpoint de telemetria")
    return client.get(
        endpoint,
        {
            "session_key": session_key,
            "driver_number": driver_number,
            "date>=": date_start,
            "date<": date_end,
        },
    )


def fetch_car_data(
    client: OpenF1Client,
    session_key: int,
    driver_number: int,
    date_start: datetime,
    date_end: datetime,
) -> Records:
    """Telemetria do carro de um piloto em uma janela de tempo."""
    return fetch_telemetry(
        client, Endpoint.CAR_DATA, session_key, driver_number, date_start, date_end
    )


def fetch_location(
    client: OpenF1Client,
    session_key: int,
    driver_number: int,
    date_start: datetime,
    date_end: datetime,
) -> Records:
    """Posição (x, y, z) de um piloto em uma janela de tempo."""
    return fetch_telemetry(
        client, Endpoint.LOCATION, session_key, driver_number, date_start, date_end
    )
