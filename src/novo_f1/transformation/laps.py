"""Regras de transformação de dados de voltas."""

from collections.abc import Iterable

import pandas as pd

from novo_f1.transformation.common import require_columns
from novo_f1.transformation.results import with_driver_info

SECTOR_COLUMNS = ["duration_sector_1", "duration_sector_2", "duration_sector_3"]
DEFAULT_OUTLIER_THRESHOLD = 1.07


def fastest_lap(lap_durations: Iterable[float | None]) -> float | None:
    """Retorna a menor duração de volta válida, ou None se não houver."""
    valid = [
        duration
        for duration in lap_durations
        if duration is not None and not pd.isna(duration)
    ]
    return min(valid, default=None)


def clean_laps(
    laps: pd.DataFrame, *, drop_pit_out: bool = True, drop_null: bool = True
) -> pd.DataFrame:
    """Remove voltas de saída dos boxes e voltas sem tempo.

    Args:
        laps: DataFrame do endpoint ``laps``.
        drop_pit_out: Remove ``is_pit_out_lap == True``.
        drop_null: Remove ``lap_duration`` nulo.
    """
    if not require_columns(laps, "lap_duration"):
        return laps.iloc[0:0] if not laps.empty else laps
    mask = pd.Series(True, index=laps.index)
    if drop_null:
        mask &= laps["lap_duration"].notna()
    if drop_pit_out and "is_pit_out_lap" in laps:
        mask &= ~laps["is_pit_out_lap"].fillna(False).astype(bool)
    return laps[mask].reset_index(drop=True)


def remove_outliers(
    laps: pd.DataFrame, threshold: float = DEFAULT_OUTLIER_THRESHOLD
) -> pd.DataFrame:
    """Remove voltas acima de ``threshold`` x mediana do piloto (SC, tráfego...)."""
    if not require_columns(laps, "driver_number", "lap_duration"):
        return laps
    median = laps.groupby("driver_number")["lap_duration"].transform("median")
    return laps[laps["lap_duration"] <= median * threshold].reset_index(drop=True)


def fastest_lap_per_driver(laps: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Melhor volta de cada piloto, ordenada, com diferença para a mais rápida."""
    valid = clean_laps(laps)
    if valid.empty:
        return pd.DataFrame(
            columns=["driver_number", "name_acronym", "lap_number", "lap_duration"]
        )
    best = valid.loc[valid.groupby("driver_number")["lap_duration"].idxmin()]
    best = with_driver_info(best, drivers).sort_values("lap_duration")
    best["delta"] = best["lap_duration"] - best["lap_duration"].min()
    return best.reset_index(drop=True)


def best_sectors(laps: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Melhor tempo de cada setor por piloto e a volta ideal (soma dos melhores)."""
    if not require_columns(laps, "driver_number", *SECTOR_COLUMNS):
        return pd.DataFrame(columns=["driver_number", *SECTOR_COLUMNS, "ideal_lap"])
    sectors = laps.groupby("driver_number")[SECTOR_COLUMNS].min().reset_index()
    sectors["ideal_lap"] = sectors[SECTOR_COLUMNS].sum(axis=1, min_count=3)
    sectors = with_driver_info(sectors, drivers)
    return sectors.sort_values("ideal_lap", na_position="last").reset_index(drop=True)


def assign_stints(laps: pd.DataFrame, stints: pd.DataFrame) -> pd.DataFrame:
    """Anexa ``stint_number``, ``compound`` e idade do pneu a cada volta."""
    result = laps.copy()
    for column in ("stint_number", "compound", "tyre_age"):
        result[column] = pd.NA
    if result.empty or not require_columns(
        stints, "driver_number", "lap_start", "lap_end"
    ):
        return result
    for stint in stints.itertuples(index=False):
        lap_end = stint.lap_end if not pd.isna(stint.lap_end) else stint.lap_start
        mask = (
            (result["driver_number"] == stint.driver_number)
            & (result["lap_number"] >= stint.lap_start)
            & (result["lap_number"] <= lap_end)
        )
        age_at_start = getattr(stint, "tyre_age_at_start", 0)
        age_at_start = 0 if pd.isna(age_at_start) else age_at_start
        result.loc[mask, "stint_number"] = stint.stint_number
        result.loc[mask, "compound"] = getattr(stint, "compound", None)
        result.loc[mask, "tyre_age"] = (
            result.loc[mask, "lap_number"] - stint.lap_start + age_at_start
        )
    return result


def stint_pace(
    laps: pd.DataFrame,
    stints: pd.DataFrame,
    drivers: pd.DataFrame,
    threshold: float = DEFAULT_OUTLIER_THRESHOLD,
) -> pd.DataFrame:
    """Ritmo médio por stint (sem pit-out laps e sem voltas lentas atípicas)."""
    columns = [
        "driver_number",
        "name_acronym",
        "stint_number",
        "compound",
        "laps",
        "mean_lap",
        "median_lap",
        "best_lap",
    ]
    valid = remove_outliers(clean_laps(laps), threshold)
    tagged = assign_stints(valid, stints).dropna(subset=["stint_number"])
    if tagged.empty:
        return pd.DataFrame(columns=columns)
    pace = (
        tagged.groupby(["driver_number", "stint_number", "compound"])["lap_duration"]
        .agg(laps="count", mean_lap="mean", median_lap="median", best_lap="min")
        .reset_index()
    )
    pace = with_driver_info(pace, drivers)
    return (
        pace[columns]
        .sort_values(["driver_number", "stint_number"])
        .reset_index(drop=True)
    )
