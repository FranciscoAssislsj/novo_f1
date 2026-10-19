"""Cliente HTTP da OpenF1 com retry, backoff e intervalo mínimo entre chamadas."""

import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from novo_f1.config.settings import Settings
from novo_f1.utils.query import FilterValue, build_query

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
NO_RESULTS_STATUS = 404


class OpenF1Client:
    """Cliente síncrono para os endpoints históricos da OpenF1.

    Args:
        settings: Configuração (URL base, timeout, retries, token...).
        http_client: Cliente ``httpx`` injetável (útil em testes).
        sleep: Função de espera injetável.
        clock: Relógio monotônico injetável.
    """

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._http = http_client or httpx.Client(timeout=settings.request_timeout)
        self._sleep = sleep
        self._clock = clock
        self._last_request_at: float | None = None
        self.request_count = 0

    def build_url(self, endpoint: str, filters: Mapping[str, FilterValue]) -> str:
        """Monta a URL completa de um endpoint com os filtros codificados."""
        url = f"{self._settings.base_url}/{endpoint.strip('/')}"
        query = build_query(filters)
        return f"{url}?{query}" if query else url

    def _headers(self) -> dict[str, str]:
        if self._settings.api_token:
            return {"Authorization": f"Bearer {self._settings.api_token}"}
        return {}

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            elapsed = self._clock() - self._last_request_at
            wait = self._settings.min_request_interval - elapsed
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._clock()

    def _backoff(self, attempt: int, response: httpx.Response | None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.replace(".", "", 1).isdigit():
                return float(retry_after)
        return self._settings.backoff_factor * (2**attempt)

    def get(
        self, endpoint: str, filters: Mapping[str, FilterValue] | None = None
    ) -> list[dict[str, Any]]:
        """Faz um GET no endpoint e devolve os registros.

        Uma resposta 404 é tratada como "sem resultados" (a OpenF1 responde
        assim a filtros sem correspondência).

        Args:
            endpoint: Nome do endpoint (ex.: ``"laps"``).
            filters: Filtros no formato aceito por `build_query`.

        Returns:
            Lista de registros JSON.

        Raises:
            httpx.HTTPStatusError: Em erro HTTP não recuperável ou após esgotar
                as tentativas.
            httpx.TransportError: Em falha de rede após esgotar as tentativas.
        """
        url = self.build_url(endpoint, filters or {})
        attempt = 0
        while True:
            self._throttle()
            self.request_count += 1
            response: httpx.Response | None = None
            try:
                response = self._http.get(url, headers=self._headers())
            except httpx.TransportError:
                if attempt >= self._settings.max_retries:
                    raise
                logger.warning("Falha de rede em %s; nova tentativa", url)
            else:
                if response.status_code == NO_RESULTS_STATUS:
                    return []
                retryable = response.status_code in RETRYABLE_STATUS
                if not retryable or attempt >= self._settings.max_retries:
                    response.raise_for_status()
                    payload = response.json()
                    return payload if isinstance(payload, list) else [payload]
                logger.warning(
                    "HTTP %s em %s; nova tentativa", response.status_code, url
                )
            self._sleep(self._backoff(attempt, response))
            attempt += 1

    def close(self) -> None:
        """Fecha o cliente HTTP subjacente."""
        self._http.close()
