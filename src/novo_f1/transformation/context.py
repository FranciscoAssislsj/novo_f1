"""Contexto da sessão: clima e direção de prova."""

import pandas as pd

from novo_f1.transformation.common import require_columns, to_utc

WEATHER_COLUMNS = [
    "date",
    "air_temperature",
    "track_temperature",
    "humidity",
    "pressure",
    "rainfall",
    "wind_direction",
    "wind_speed",
]

TEMPERATURE_COLUMNS = ("air_temperature", "track_temperature")

RACE_CONTROL_COLUMNS = [
    "date",
    "lap_number",
    "category",
    "flag",
    "scope",
    "sector",
    "driver_number",
    "message",
]

NEUTRALISATION_CATEGORIES = frozenset({"SafetyCar"})
TRACK_FLAGS = frozenset({"RED", "YELLOW", "DOUBLE YELLOW", "CHEQUERED", "GREEN"})


def weather_series(weather: pd.DataFrame) -> pd.DataFrame:
    """Série temporal de clima com ``rainfall`` booleano.

    Leituras de exatamente 0 °C são falhas do sensor (nenhuma sessão de F1
    ocorre com ar ou pista a 0 °C) e viram nulas.
    """
    if not require_columns(weather, "date"):
        return pd.DataFrame(columns=WEATHER_COLUMNS)
    series = weather.copy()
    for column in WEATHER_COLUMNS:
        if column not in series:
            series[column] = pd.NA
    series["date"] = to_utc(series["date"])
    for column in TEMPERATURE_COLUMNS:
        values = pd.to_numeric(series[column], errors="coerce")
        series[column] = values.mask(values == 0)
    series["rainfall"] = (
        pd.to_numeric(series["rainfall"], errors="coerce").fillna(0) > 0
    )
    return series[WEATHER_COLUMNS].sort_values("date").reset_index(drop=True)


def weather_summary(weather: pd.DataFrame) -> dict[str, float | bool | None]:
    """Mínimos/máximos de temperatura e se choveu na sessão."""
    series = weather_series(weather)
    if series.empty:
        return {
            "air_min": None,
            "air_max": None,
            "track_min": None,
            "track_max": None,
            "rain": False,
        }

    def _stat(column: str, how: str) -> float | None:
        value = pd.to_numeric(series[column], errors="coerce").agg(how)
        return None if pd.isna(value) else float(value)

    return {
        "air_min": _stat("air_temperature", "min"),
        "air_max": _stat("air_temperature", "max"),
        "track_min": _stat("track_temperature", "min"),
        "track_max": _stat("track_temperature", "max"),
        "rain": bool(series["rainfall"].any()),
    }


def race_control_events(race_control: pd.DataFrame) -> pd.DataFrame:
    """Mensagens da direção de prova, em ordem cronológica."""
    if not require_columns(race_control, "date", "message"):
        return pd.DataFrame(columns=RACE_CONTROL_COLUMNS)
    events = race_control.copy()
    for column in RACE_CONTROL_COLUMNS:
        if column not in events:
            events[column] = pd.NA
    events["date"] = to_utc(events["date"])
    return events[RACE_CONTROL_COLUMNS].sort_values("date").reset_index(drop=True)


def key_events(race_control: pd.DataFrame) -> pd.DataFrame:
    """Eventos relevantes: safety car/VSC e bandeiras de pista inteira."""
    events = race_control_events(race_control)
    if events.empty:
        return events
    is_neutralisation = events["category"].isin(NEUTRALISATION_CATEGORIES)
    is_track_flag = (events["category"] == "Flag") & (
        events["scope"].fillna("Track") == "Track"
    )
    is_track_flag &= events["flag"].isin(TRACK_FLAGS)
    return events[is_neutralisation | is_track_flag].reset_index(drop=True)
