"""Evolução de posições e gaps ao longo da sessão."""

import re
from typing import Any

import pandas as pd

from novo_f1.transformation.common import require_columns, to_utc
from novo_f1.transformation.results import parse_gap, with_driver_info

_LAPS_DOWN = re.compile(r"\+?\s*(\d+)\s*LAPS?", re.IGNORECASE)


def laps_down(value: Any) -> int:
    """Número de voltas de atraso em textos como ``"+1 LAP"`` (0 se não houver)."""
    if not isinstance(value, str):
        return 0
    match = _LAPS_DOWN.search(value)
    return int(match.group(1)) if match else 0


def position_changes(position: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Mudanças de posição com data em UTC e dados do piloto, ordenadas."""
    if not require_columns(position, "driver_number", "position", "date"):
        return pd.DataFrame(columns=["date", "driver_number", "position"])
    changes = position.copy()
    changes["date"] = to_utc(changes["date"])
    changes = with_driver_info(changes, drivers)
    return changes.sort_values(["date", "position"]).reset_index(drop=True)


def position_by_lap(position: pd.DataFrame, laps: pd.DataFrame) -> pd.DataFrame:
    """Posição de cada piloto ao fim de cada volta.

    Cada mudança de posição é associada à volta em andamento naquele instante
    (pelo ``date_start`` das voltas do piloto); vale a última posição da volta.
    Mudanças antes da primeira volta contam como volta 0 (grid).

    Returns:
        Colunas ``driver_number, lap_number, position``.
    """
    columns = ["driver_number", "lap_number", "position"]
    if not (
        require_columns(position, "driver_number", "position", "date")
        and require_columns(laps, "driver_number", "lap_number", "date_start")
    ):
        return pd.DataFrame(columns=columns)
    changes = position[["driver_number", "position", "date"]].copy()
    changes["date"] = to_utc(changes["date"])
    starts = laps[["driver_number", "lap_number", "date_start"]].copy()
    starts["date_start"] = to_utc(starts["date_start"])
    starts = starts.dropna(subset=["date_start"]).sort_values("date_start")
    changes = changes.dropna(subset=["date"]).sort_values("date")
    merged = pd.merge_asof(
        changes,
        starts,
        left_on="date",
        right_on="date_start",
        by="driver_number",
        direction="backward",
    )
    merged["lap_number"] = merged["lap_number"].fillna(0).astype(int)
    per_lap = (
        merged.sort_values("date")
        .groupby(["driver_number", "lap_number"], as_index=False)
        .last()[columns]
    )
    return _forward_fill_laps(per_lap, starts)


def _forward_fill_laps(per_lap: pd.DataFrame, starts: pd.DataFrame) -> pd.DataFrame:
    """Repete a última posição conhecida nas voltas sem mudança."""
    filled: list[pd.DataFrame] = []
    for driver, group in per_lap.groupby("driver_number"):
        driver_laps = starts.loc[starts["driver_number"] == driver, "lap_number"]
        last_lap = int(max(driver_laps.max(), group["lap_number"].max()))
        frame = (
            group.set_index("lap_number")
            .reindex(range(0, last_lap + 1))
            .ffill()
            .dropna(subset=["position"])
            .reset_index()
        )
        frame["driver_number"] = driver
        filled.append(frame)
    result = pd.concat(filled, ignore_index=True)
    result["position"] = result["position"].astype(int)
    return result[["driver_number", "lap_number", "position"]]


def gaps_series(intervals: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Série de gaps (s) para o líder e para o carro à frente.

    ``"+N LAP(S)"`` vira gap nulo e ``laps_down = N``. O líder é a amostra com
    ``gap_to_leader`` **e** ``interval`` nulos (gap 0); um ``gap_to_leader``
    nulo com ``interval`` preenchido é ruído da API e fica nulo.
    """
    columns = ["date", "driver_number", "gap_to_leader", "interval", "laps_down"]
    if not require_columns(intervals, "driver_number", "date"):
        return pd.DataFrame(columns=columns)
    gaps = intervals.copy()
    gaps["date"] = to_utc(gaps["date"])
    raw_leader = gaps.get("gap_to_leader", pd.Series(None, index=gaps.index))
    raw_interval = gaps.get("interval", pd.Series(None, index=gaps.index))
    gaps["laps_down"] = raw_leader.map(laps_down)
    is_leader = raw_leader.isna() & raw_interval.isna()
    gaps["gap_to_leader"] = [parse_gap(value)[0] for value in raw_leader]
    gaps["interval"] = [parse_gap(value)[0] for value in raw_interval]
    gaps.loc[is_leader, ["gap_to_leader", "interval"]] = 0.0
    gaps = with_driver_info(gaps, drivers)
    return gaps.sort_values("date").reset_index(drop=True)
