"""Cache local em Parquet, particionado por endpoint e ano."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_SCALAR_TYPES = (str, int, float, bool)


def partition_name(**parts: object) -> str:
    """Monta o nome do arquivo a partir de pares chave=valor.

    Example:
        >>> partition_name(session_key=9161, driver=1, lap=5)
        'session_key=9161_driver=1_lap=5'
    """
    return "_".join(f"{key}={value}" for key, value in parts.items())


def _value_kind(value: Any) -> str:
    if isinstance(value, list | tuple | np.ndarray):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "number"
    return type(value).__name__


def _to_text(value: Any) -> str:
    if isinstance(value, list | tuple | dict):
        return json.dumps(value)
    if isinstance(value, np.ndarray):
        return json.dumps(value.tolist())
    return str(value)


def coerce_mixed_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Converte para texto colunas `object` com tipos misturados.

    O Parquet exige um tipo por coluna. Campos como ``gap_to_leader`` misturam
    números e textos (``"+1 LAP"``); nesses casos os valores não nulos viram
    texto e a transformação faz o parsing.

    Args:
        frame: DataFrame vindo da API.

    Returns:
        Cópia do DataFrame com tipos consistentes por coluna.
    """
    result = frame.copy()
    for column in result.columns:
        if result[column].dtype != object:
            continue
        values = result[column].dropna()
        kinds = {_value_kind(value) for value in values}
        if len(kinds) > 1:
            result[column] = result[column].map(
                lambda value: None if _is_missing(value) else _to_text(value)
            )
    return result


def _is_missing(value: Any) -> bool:
    if isinstance(value, list | tuple | dict | np.ndarray):
        return False
    return bool(pd.isna(value))


class ParquetStore:
    """Lê e grava DataFrames em ``<root>/raw/<endpoint>/year=<ano>/<nome>.parquet``.

    Args:
        root: Diretório raiz do cache (``DATA_DIR``).
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, endpoint: str, year: int, name: str) -> Path:
        """Caminho do arquivo de cache."""
        return self.root / "raw" / endpoint / f"year={year}" / f"{name}.parquet"

    def exists(self, path: Path) -> bool:
        """Indica se o arquivo existe."""
        return path.is_file()

    def is_expired(
        self, path: Path, ttl: timedelta, now: datetime | None = None
    ) -> bool:
        """Indica se o arquivo é mais antigo que ``ttl`` (ou não existe)."""
        if not self.exists(path):
            return True
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return (now or datetime.now(UTC)) - modified > ttl

    def save(self, frame: pd.DataFrame, path: Path) -> Path:
        """Grava o DataFrame em Parquet, criando os diretórios necessários."""
        path.parent.mkdir(parents=True, exist_ok=True)
        coerce_mixed_columns(frame).to_parquet(path, index=False)
        return path

    def load(self, path: Path) -> pd.DataFrame:
        """Lê um arquivo Parquet do cache."""
        return pd.read_parquet(path)
