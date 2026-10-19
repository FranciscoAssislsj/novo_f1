"""Pré-carregamento do cache local (sem telemetria)."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pandas as pd

from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.services.repository import Repository

logger = logging.getLogger(__name__)

SESSION_ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint.DRIVERS,
    Endpoint.SESSION_RESULT,
    Endpoint.LAPS,
    Endpoint.STINTS,
    Endpoint.PIT,
    Endpoint.POSITION,
)
"""Endpoints pré-carregados para qualquer sessão."""

QUALIFYING_ENDPOINTS: tuple[Endpoint, ...] = (Endpoint.STARTING_GRID,)
"""Endpoints pré-carregados apenas em classificações.

A OpenF1 associa o grid de largada à classificação que o definiu, e não à
corrida (ver `grid_session_key`).
"""


@dataclass
class SyncReport:
    """Resumo de uma execução de sync."""

    sessions: list[int] = field(default_factory=list)
    rows: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_rows(self, endpoint: str, count: int) -> None:
        """Acumula o total de linhas carregadas por endpoint."""
        self.rows[endpoint] = self.rows.get(endpoint, 0) + count


def finished_sessions(sessions: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """Filtra sessões já encerradas e não canceladas.

    Args:
        sessions: DataFrame do endpoint ``sessions``.
        now: Instante de referência (UTC).

    Returns:
        Sessões com ``date_end`` anterior a ``now``.
    """
    if sessions.empty or "date_end" not in sessions:
        return sessions.iloc[0:0]
    date_end = pd.to_datetime(sessions["date_end"], utc=True, format="ISO8601")
    mask = date_end < pd.Timestamp(now)
    if "is_cancelled" in sessions:
        mask &= ~sessions["is_cancelled"].fillna(False).astype(bool)
    return sessions[mask]


def sync_season(
    repository: Repository,
    year: int,
    session_key: int | None = None,
    now: datetime | None = None,
) -> SyncReport:
    """Carrega calendário, pilotos, resultados, voltas e estratégia no cache.

    Args:
        repository: Repositório cache-or-fetch.
        year: Temporada.
        session_key: Se informado, sincroniza só essa sessão.
        now: Instante de referência (UTC); padrão é o horário atual.

    Returns:
        Relatório com sessões processadas, linhas por endpoint e erros.
    """
    report = SyncReport()
    report.add_rows(Endpoint.MEETINGS, len(repository.meetings(year)))
    sessions = repository.sessions(year)
    report.add_rows(Endpoint.SESSIONS, len(sessions))

    targets = finished_sessions(sessions, now or datetime.now(UTC))
    if session_key is not None:
        targets = targets[targets["session_key"] == session_key]

    for row in targets.itertuples(index=False):
        key = int(row.session_key)
        session_type = getattr(row, "session_type", None)
        endpoints = SESSION_ENDPOINTS
        if session_type == "Qualifying":
            endpoints = SESSION_ENDPOINTS + QUALIFYING_ENDPOINTS
        for endpoint in endpoints:
            try:
                frame = repository.session_data(endpoint, key, year, session_type)
            except Exception as error:  # segue com as demais sessões
                logger.error("Falha em %s/%s: %s", endpoint, key, error)
                report.errors.append(f"{endpoint}/{key}: {error}")
                continue
            report.add_rows(endpoint, len(frame))
        report.sessions.append(key)
        logger.info("Sessão %s sincronizada", key)
    return report
