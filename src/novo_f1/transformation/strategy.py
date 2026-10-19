"""Estratégia: linha do tempo de pneus e resumo de pit stops."""

import pandas as pd

from novo_f1.transformation.common import require_columns
from novo_f1.transformation.results import with_driver_info

COMPOUND_COLOURS = {
    "SOFT": "#DA291C",
    "MEDIUM": "#FFD12E",
    "HARD": "#F0F0EC",
    "INTERMEDIATE": "#43B02A",
    "WET": "#0067AD",
    "UNKNOWN": "#8A8A8A",
}
"""Cores convencionais dos compostos da Pirelli."""

TIMELINE_COLUMNS = [
    "driver_number",
    "name_acronym",
    "stint_number",
    "compound",
    "lap_start",
    "lap_end",
    "laps",
    "tyre_age_at_start",
    "colour",
]


def compound_colour(compound: object) -> str:
    """Cor do composto (cinza para desconhecido/nulo)."""
    key = str(compound).upper() if isinstance(compound, str) else "UNKNOWN"
    return COMPOUND_COLOURS.get(key, COMPOUND_COLOURS["UNKNOWN"])


def tyre_timeline(stints: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Stints prontos para um gráfico de Gantt (um retângulo por stint).

    ``lap_end`` nulo (stint em andamento ou de uma volta) usa ``lap_start``.
    """
    if not require_columns(stints, "driver_number", "lap_start"):
        return pd.DataFrame(columns=TIMELINE_COLUMNS)
    timeline = stints.dropna(subset=["lap_start"]).copy()
    if "lap_end" not in timeline:
        timeline["lap_end"] = pd.NA
    timeline["lap_end"] = timeline["lap_end"].fillna(timeline["lap_start"])
    timeline["lap_start"] = timeline["lap_start"].astype(int)
    timeline["lap_end"] = timeline["lap_end"].astype(int)
    timeline["laps"] = timeline["lap_end"] - timeline["lap_start"] + 1
    if "compound" not in timeline:
        timeline["compound"] = "UNKNOWN"
    timeline["compound"] = timeline["compound"].fillna("UNKNOWN").str.upper()
    if "tyre_age_at_start" not in timeline:
        timeline["tyre_age_at_start"] = pd.NA
    timeline["colour"] = timeline["compound"].map(compound_colour)
    timeline = with_driver_info(timeline, drivers)
    return (
        timeline[TIMELINE_COLUMNS]
        .sort_values(["driver_number", "stint_number"])
        .reset_index(drop=True)
    )


def pit_summary(pit: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Paradas com tempo no pit lane e tempo parado.

    Usa ``lane_duration`` (``pit_duration`` é depreciado e só é lido como
    alternativa quando ``lane_duration`` não vier). ``stop_duration`` só existe
    a partir do GP dos EUA de 2024; antes disso fica nulo.
    """
    columns = [
        "driver_number",
        "name_acronym",
        "team_colour",
        "lap_number",
        "lane_duration",
        "stop_duration",
    ]
    if not require_columns(pit, "driver_number", "lap_number"):
        return pd.DataFrame(columns=columns)
    summary = pit.copy()
    if "lane_duration" not in summary:
        summary["lane_duration"] = summary.get("pit_duration", pd.NA)
    elif "pit_duration" in summary:
        summary["lane_duration"] = summary["lane_duration"].fillna(
            summary["pit_duration"]
        )
    if "stop_duration" not in summary:
        summary["stop_duration"] = pd.NA
    summary["lane_duration"] = pd.to_numeric(summary["lane_duration"], errors="coerce")
    summary["stop_duration"] = pd.to_numeric(summary["stop_duration"], errors="coerce")
    summary = with_driver_info(summary, drivers)
    return (
        summary[columns]
        .sort_values(["lap_number", "driver_number"])
        .reset_index(drop=True)
    )


def pit_stop_counts(pit_stops: pd.DataFrame) -> pd.DataFrame:
    """Número de paradas e tempo médio/mínimo no pit lane por piloto."""
    if pit_stops.empty:
        return pd.DataFrame(
            columns=["name_acronym", "stops", "best_lane", "mean_lane", "best_stop"]
        )
    return (
        pit_stops.groupby("name_acronym")
        .agg(
            stops=("lap_number", "count"),
            best_lane=("lane_duration", "min"),
            mean_lane=("lane_duration", "mean"),
            best_stop=("stop_duration", "min"),
        )
        .reset_index()
        .sort_values("best_lane", na_position="last")
        .reset_index(drop=True)
    )
