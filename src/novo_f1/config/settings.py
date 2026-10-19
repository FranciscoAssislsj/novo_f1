"""Configurações do projeto lidas de variáveis de ambiente."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://api.openf1.org/v1"


@dataclass(frozen=True)
class Settings:
    """Parâmetros de execução do cliente HTTP e do cache local.

    Attributes:
        base_url: URL base da OpenF1 API (sem barra final).
        api_token: Token opcional; só é enviado se estiver definido.
        data_dir: Diretório raiz do cache em Parquet.
        request_timeout: Timeout de cada requisição, em segundos.
        max_retries: Número máximo de novas tentativas em 429/5xx/erro de rede.
        min_request_interval: Intervalo mínimo entre requisições, em segundos.
        backoff_factor: Fator base do backoff exponencial, em segundos.
        calendar_ttl_hours: Validade do cache de meetings/sessions do ano corrente.
    """

    base_url: str = DEFAULT_BASE_URL
    api_token: str | None = None
    data_dir: Path = Path("data")
    request_timeout: float = 30.0
    max_retries: int = 3
    min_request_interval: float = 0.35
    backoff_factor: float = 1.0
    calendar_ttl_hours: float = 24.0


def load_settings() -> Settings:
    """Monta um `Settings` a partir das variáveis de ambiente.

    Returns:
        Configuração com os valores do ambiente ou os padrões.
    """
    return Settings(
        base_url=os.getenv("OPENF1_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        api_token=os.getenv("OPENF1_API_TOKEN") or None,
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        min_request_interval=float(os.getenv("MIN_REQUEST_INTERVAL", "0.35")),
        backoff_factor=float(os.getenv("BACKOFF_FACTOR", "1.0")),
        calendar_ttl_hours=float(os.getenv("CALENDAR_TTL_HOURS", "24")),
    )
