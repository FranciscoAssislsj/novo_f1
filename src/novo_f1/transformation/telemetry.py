"""Telemetria por volta: janela de tempo, preparo dos dados e DRS."""

from typing import Any

import pandas as pd

from novo_f1.transformation.common import require_columns, to_utc

DRS_OFF = "Desligado"
DRS_ELIGIBLE = "Habilitado"
DRS_ON = "Ligado"
DRS_UNKNOWN = "Desconhecido"

DRS_STATES: dict[int, str] = {
    0: DRS_OFF,
    1: DRS_OFF,
    8: DRS_ELIGIBLE,
    10: DRS_ON,
    12: DRS_ON,
    14: DRS_ON,
}
"""Tabela de referência de ``car_data.drs`` (demais valores: desconhecido)."""

LAP_WINDOW_MARGIN = pd.Timedelta(seconds=1)
FALLBACK_LAP_LENGTH = pd.Timedelta(minutes=3)
MERGE_TOLERANCE = pd.Timedelta(milliseconds=500)


def decode_drs(value: Any) -> str:
    """Traduz o código numérico de DRS para um estado legível."""
    try:
        code = int(value)
    except TypeError, ValueError:
        return DRS_UNKNOWN
    return DRS_STATES.get(code, DRS_UNKNOWN)


def lap_window(
    laps: pd.DataFrame, driver_number: int, lap_number: int
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Janela ``[início, fim)`` de uma volta de um piloto.

    O fim é o início da volta seguinte; sem ela, usa ``date_start +
    lap_duration`` (mais uma margem) ou, se o tempo também faltar, 3 minutos.

    Returns:
        ``(início, fim)`` em UTC ou ``None`` se a volta não tiver início.
    """
    if not require_columns(laps, "driver_number", "lap_number", "date_start"):
        return None
    driver_laps = laps[laps["driver_number"] == driver_number].copy()
    driver_laps["date_start"] = to_utc(driver_laps["date_start"])
    current = driver_laps[driver_laps["lap_number"] == lap_number]
    if current.empty or pd.isna(current["date_start"].iloc[0]):
        return None
    start = current["date_start"].iloc[0]
    following = driver_laps[driver_laps["lap_number"] == lap_number + 1]
    if not following.empty and not pd.isna(following["date_start"].iloc[0]):
        return start, following["date_start"].iloc[0]
    duration = current["lap_duration"].iloc[0] if "lap_duration" in current else None
    if duration is None or pd.isna(duration):
        return start, start + FALLBACK_LAP_LENGTH
    return start, start + pd.Timedelta(seconds=float(duration)) + LAP_WINDOW_MARGIN


def prepare_car_data(car_data: pd.DataFrame) -> pd.DataFrame:
    """Ordena por tempo e adiciona ``elapsed_s``, ``distance_m`` e ``drs_state``.

    A distância é aproximada integrando a velocidade (km/h) no tempo, o que
    permite sobrepor voltas de pilotos diferentes no mesmo eixo.
    """
    if not require_columns(car_data, "date", "speed"):
        return pd.DataFrame(
            columns=["date", "speed", "elapsed_s", "distance_m", "drs_state"]
        )
    telemetry = car_data.copy()
    telemetry["date"] = to_utc(telemetry["date"])
    telemetry = telemetry.dropna(subset=["date"]).sort_values("date")
    elapsed = (telemetry["date"] - telemetry["date"].iloc[0]).dt.total_seconds()
    telemetry["elapsed_s"] = elapsed
    step = elapsed.diff().fillna(0)
    speed_ms = pd.to_numeric(telemetry["speed"], errors="coerce").fillna(0) / 3.6
    telemetry["distance_m"] = (speed_ms * step).cumsum()
    telemetry["drs_state"] = telemetry.get("drs", pd.Series(dtype=float)).map(
        decode_drs
    )
    return telemetry.reset_index(drop=True)


def merge_car_location(car_data: pd.DataFrame, location: pd.DataFrame) -> pd.DataFrame:
    """Une telemetria e posição (x, y) pela amostra mais próxima no tempo.

    Args:
        car_data: Saída de `prepare_car_data`.
        location: DataFrame do endpoint ``location``.

    Returns:
        ``car_data`` com as colunas ``x`` e ``y`` (nulas se não houver amostra
        a até 500 ms).
    """
    if car_data.empty or not require_columns(location, "date", "x", "y"):
        result = car_data.copy()
        result["x"] = pd.NA
        result["y"] = pd.NA
        return result
    points = location[["date", "x", "y"]].copy()
    points["date"] = to_utc(points["date"])
    points = points.dropna(subset=["date"]).sort_values("date")
    return pd.merge_asof(
        car_data.sort_values("date"),
        points,
        on="date",
        direction="nearest",
        tolerance=MERGE_TOLERANCE,
    )
