"""Calendário da temporada a partir de ``meetings`` e ``sessions``."""

import pandas as pd

from novo_f1.transformation.common import require_columns, to_utc

CALENDAR_COLUMNS = [
    "meeting_key",
    "meeting_name",
    "country_name",
    "location",
    "circuit_short_name",
    "circuit_type",
    "date_start",
    "date_end",
    "is_cancelled",
    "is_testing",
    "sessions",
    "has_sprint",
]


def season_calendar(meetings: pd.DataFrame, sessions: pd.DataFrame) -> pd.DataFrame:
    """Monta o calendário da temporada, um meeting por linha, ordenado por data.

    Args:
        meetings: DataFrame do endpoint ``meetings``.
        sessions: DataFrame do endpoint ``sessions``.

    Returns:
        DataFrame com as colunas de `CALENDAR_COLUMNS`.
    """
    if not require_columns(meetings, "meeting_key", "date_start"):
        return pd.DataFrame(columns=CALENDAR_COLUMNS)
    calendar = meetings.copy()
    for column in CALENDAR_COLUMNS:
        if column not in calendar:
            calendar[column] = pd.NA
    calendar["date_start"] = to_utc(calendar["date_start"])
    calendar["date_end"] = to_utc(calendar["date_end"])
    calendar["is_cancelled"] = calendar["is_cancelled"].fillna(False).astype(bool)
    calendar["is_testing"] = (
        calendar["meeting_name"].fillna("").str.contains("Testing", case=False)
    )

    if require_columns(sessions, "meeting_key", "session_name"):
        grouped = sessions.groupby("meeting_key")["session_name"]
        counts = grouped.size()
        sprint = grouped.apply(lambda names: bool((names == "Sprint").any()))
        calendar["sessions"] = calendar["meeting_key"].map(counts).fillna(0)
        calendar["has_sprint"] = calendar["meeting_key"].map(sprint).fillna(False)
    else:
        calendar["sessions"] = 0
        calendar["has_sprint"] = False
    calendar["sessions"] = calendar["sessions"].astype(int)
    calendar["has_sprint"] = calendar["has_sprint"].astype(bool)
    return calendar[CALENDAR_COLUMNS].sort_values("date_start").reset_index(drop=True)


def meeting_sessions(sessions: pd.DataFrame, meeting_key: int) -> pd.DataFrame:
    """Sessões de um meeting, ordenadas pelo início."""
    if not require_columns(sessions, "meeting_key", "date_start"):
        return sessions.iloc[0:0]
    selected = sessions[sessions["meeting_key"] == meeting_key].copy()
    selected["date_start"] = to_utc(selected["date_start"])
    return selected.sort_values("date_start").reset_index(drop=True)


def available_meetings(calendar: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    """Meetings já iniciados e não cancelados (os que podem ter dados)."""
    if calendar.empty:
        return calendar
    mask = (calendar["date_start"] <= now) & ~calendar["is_cancelled"]
    return calendar[mask].reset_index(drop=True)


def grid_session_key(sessions: pd.DataFrame, session_key: int) -> int | None:
    """Sessão que guarda o ``starting_grid`` de uma corrida (Race ou Sprint).

    Na OpenF1 o grid de largada fica associado à classificação que o definiu:
    a última sessão do tipo ``Qualifying`` do mesmo meeting antes da corrida
    (``Qualifying`` para a Race; ``Sprint Qualifying`` para a Sprint).

    Returns:
        ``session_key`` da classificação, ou ``None`` se não houver.
    """
    if not require_columns(sessions, "session_key", "meeting_key", "session_type"):
        return None
    target = sessions[sessions["session_key"] == session_key]
    if target.empty:
        return None
    meeting = meeting_sessions(sessions, int(target["meeting_key"].iloc[0]))
    start = meeting.loc[meeting["session_key"] == session_key, "date_start"].iloc[0]
    qualifying = meeting[
        (meeting["session_type"] == "Qualifying") & (meeting["date_start"] < start)
    ]
    return None if qualifying.empty else int(qualifying["session_key"].iloc[-1])
