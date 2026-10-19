"""Acesso "cache-or-fetch": lê do Parquet local ou busca na API e grava."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from novo_f1.config.settings import Settings, load_settings
from novo_f1.ingestion.client import OpenF1Client
from novo_f1.ingestion.endpoints import (
    RACE_ONLY_ENDPOINTS,
    TELEMETRY_ENDPOINTS,
    Endpoint,
    fetch,
    fetch_telemetry,
    is_race_session,
)
from novo_f1.storage.parquet_store import ParquetStore, partition_name

logger = logging.getLogger(__name__)


class Repository:
    """Fonte única de DataFrames para o CLI e o dashboard.

    O histórico é imutável: se o arquivo do cache existe, a API não é chamada.
    A exceção são ``meetings`` e ``sessions`` do ano corrente, que expiram após
    ``calendar_ttl_hours``. Respostas vazias não são gravadas, para que dados
    publicados mais tarde (ex.: resultado oficial) sejam buscados de novo.

    Args:
        client: Cliente da OpenF1.
        store: Cache em Parquet.
        calendar_ttl: Validade do calendário do ano corrente.
        now: Relógio injetável (UTC).
    """

    def __init__(
        self,
        client: OpenF1Client,
        store: ParquetStore,
        calendar_ttl: timedelta = timedelta(hours=24),
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.client = client
        self.store = store
        self.calendar_ttl = calendar_ttl
        self._now = now

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Repository:
        """Cria um repositório com cliente e cache a partir da configuração."""
        settings = settings or load_settings()
        return cls(
            client=OpenF1Client(settings),
            store=ParquetStore(settings.data_dir),
            calendar_ttl=timedelta(hours=settings.calendar_ttl_hours),
        )

    def _cached(
        self,
        path: Path,
        fetcher: Callable[[], list[dict]],
        ttl: timedelta | None = None,
    ) -> pd.DataFrame:
        fresh = self.store.exists(path) and (
            ttl is None or not self.store.is_expired(path, ttl, self._now())
        )
        if fresh:
            logger.debug("Cache hit: %s", path)
            return self.store.load(path)
        frame = pd.DataFrame.from_records(fetcher())
        if not frame.empty:
            self.store.save(frame, path)
        return frame

    def _calendar(self, endpoint: Endpoint, year: int) -> pd.DataFrame:
        path = self.store.path_for(endpoint, year, "all")
        ttl = self.calendar_ttl if year >= self._now().year else None
        return self._cached(path, lambda: fetch(self.client, endpoint, year=year), ttl)

    def meetings(self, year: int) -> pd.DataFrame:
        """Meetings da temporada."""
        return self._calendar(Endpoint.MEETINGS, year)

    def sessions(self, year: int) -> pd.DataFrame:
        """Sessões da temporada."""
        return self._calendar(Endpoint.SESSIONS, year)

    def session_data(
        self,
        endpoint: str,
        session_key: int,
        year: int,
        session_type: str | None = None,
    ) -> pd.DataFrame:
        """Dados de um endpoint por sessão (``drivers``, ``laps``, ``pit``...).

        Args:
            endpoint: Nome do endpoint.
            session_key: Chave da sessão.
            year: Temporada (usada na partição do cache).
            session_type: Tipo da sessão; se informado e não for corrida, os
                endpoints só de corrida devolvem um DataFrame vazio sem chamar
                a API.

        Raises:
            ValueError: Se o endpoint for de telemetria (use `lap_telemetry`).
        """
        if endpoint in TELEMETRY_ENDPOINTS:
            raise ValueError(f"{endpoint} deve ser buscado com lap_telemetry()")
        if (
            endpoint in RACE_ONLY_ENDPOINTS
            and session_type is not None
            and not is_race_session(session_type)
        ):
            return pd.DataFrame()
        path = self.store.path_for(
            endpoint, year, partition_name(session_key=session_key)
        )
        return self._cached(
            path, lambda: fetch(self.client, endpoint, session_key=session_key)
        )

    def lap_telemetry(
        self,
        endpoint: str,
        session_key: int,
        year: int,
        driver_number: int,
        lap_number: int,
        window: tuple[datetime, datetime],
    ) -> pd.DataFrame:
        """Telemetria (``car_data``/``location``) de uma volta de um piloto.

        Args:
            endpoint: ``car_data`` ou ``location``.
            session_key: Chave da sessão.
            year: Temporada.
            driver_number: Número do piloto.
            lap_number: Número da volta (só identifica o arquivo de cache).
            window: Intervalo ``[início, fim)`` da volta.

        Raises:
            ValueError: Se o endpoint não for de telemetria.
        """
        name = partition_name(
            session_key=session_key, driver=driver_number, lap=lap_number
        )
        path = self.store.path_for(endpoint, year, name)
        start, end = window
        return self._cached(
            path,
            lambda: fetch_telemetry(
                self.client, endpoint, session_key, driver_number, start, end
            ),
        )
