"""Utilitários compartilhados pelas transformações."""

import json
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_TEAM_COLOUR = "#7F7F7F"


def to_utc(values: pd.Series) -> pd.Series:
    """Converte uma série de datas ISO 8601 (com ou sem fuso) para UTC.

    A resolução é fixada em nanossegundos para que séries de origens diferentes
    possam ser combinadas (``merge_asof`` exige o mesmo dtype).
    """
    parsed = pd.to_datetime(values, utc=True, format="ISO8601", errors="coerce")
    return parsed.dt.as_unit("ns")


def as_list(value: Any) -> list[Any] | None:
    """Normaliza um valor de array (lista, ndarray do Parquet ou JSON em texto).

    Returns:
        A lista correspondente, ou ``None`` se o valor não for um array.
    """
    if isinstance(value, list | tuple):
        return list(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, str) and value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, list) else None
    return None


def to_float(value: Any) -> float | None:
    """Converte para float; devolve ``None`` para nulos e textos não numéricos."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float | np.number):
        return None if pd.isna(value) else float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def normalize_colour(value: Any) -> str:
    """Converte ``RRGGBB`` da API para ``#RRGGBB``; usa cinza se ausente."""
    if not isinstance(value, str) or not value.strip():
        return DEFAULT_TEAM_COLOUR
    colour = value.strip().lstrip("#")
    if len(colour) != 6:
        return DEFAULT_TEAM_COLOUR
    return f"#{colour.upper()}"


def require_columns(frame: pd.DataFrame, *columns: str) -> bool:
    """Indica se o DataFrame não está vazio e tem todas as colunas."""
    return not frame.empty and all(column in frame.columns for column in columns)
