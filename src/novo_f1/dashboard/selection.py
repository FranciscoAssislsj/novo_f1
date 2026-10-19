"""Seleção ano → meeting → sessão → pilotos, guardada em ``st.session_state``."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pandas as pd
import streamlit as st

from novo_f1.dashboard.data import (
    load_meetings,
    load_session_data,
    load_sessions,
    safe_load,
)
from novo_f1.ingestion.endpoints import Endpoint, is_race_session
from novo_f1.transformation.calendar import (
    available_meetings,
    meeting_sessions,
    season_calendar,
)
from novo_f1.transformation.results import classification, driver_info

FIRST_YEAR = 2023
DEFAULT_DRIVER_COUNT = 3
SELECTION_KEY = "selection"


@dataclass(frozen=True)
class Selection:
    """Contexto escolhido na barra lateral."""

    year: int
    meeting_key: int
    meeting_name: str
    session_key: int
    session_name: str
    session_type: str | None
    driver_numbers: tuple[int, ...] = field(default_factory=tuple)

    @property
    def is_race(self) -> bool:
        """Indica se a sessão é corrida (Race ou Sprint)."""
        return is_race_session(self.session_type)


def season_years(now: datetime) -> list[int]:
    """Temporadas disponíveis, da mais recente para a mais antiga."""
    return list(range(max(now.year, FIRST_YEAR), FIRST_YEAR - 1, -1))


def default_session_index(sessions: pd.DataFrame) -> int:
    """Índice padrão: a corrida principal, senão a última sessão."""
    if sessions.empty:
        return 0
    names = sessions["session_name"].tolist()
    return names.index("Race") if "Race" in names else len(names) - 1


def default_drivers(
    drivers: pd.DataFrame,
    session_result: pd.DataFrame,
    count: int = DEFAULT_DRIVER_COUNT,
) -> list[int]:
    """Os ``count`` primeiros da classificação (ou os primeiros números)."""
    ranked = classification(session_result, drivers)
    if not ranked.empty:
        return ranked["driver_number"].head(count).astype(int).tolist()
    return driver_info(drivers)["driver_number"].head(count).astype(int).tolist()


def render_sidebar() -> Selection | None:
    """Desenha os seletores na barra lateral e grava a seleção no estado."""
    now = datetime.now(UTC)
    sidebar = st.sidebar
    sidebar.header("Seleção")
    year = sidebar.selectbox("Temporada", season_years(now), key="year")

    meetings = safe_load(load_meetings, year)
    sessions = safe_load(load_sessions, year)
    calendar = available_meetings(
        season_calendar(meetings, sessions), pd.Timestamp(now)
    )
    if calendar.empty:
        sidebar.info("Nenhum Grande Prêmio disponível nesta temporada.")
        st.session_state[SELECTION_KEY] = None
        return None

    names = dict(zip(calendar["meeting_key"], calendar["meeting_name"], strict=True))
    meeting_keys = list(reversed(names))
    meeting_key = sidebar.selectbox(
        "Grande Prêmio", meeting_keys, format_func=names.__getitem__, key="meeting"
    )

    options = meeting_sessions(sessions, meeting_key)
    options = options[options["date_start"] <= pd.Timestamp(now)].reset_index(drop=True)
    if options.empty:
        sidebar.info("Nenhuma sessão iniciada neste Grande Prêmio.")
        st.session_state[SELECTION_KEY] = None
        return None
    session_index = sidebar.selectbox(
        "Sessão",
        list(options.index),
        index=default_session_index(options),
        format_func=lambda index: options.loc[index, "session_name"],
        key=f"session_{meeting_key}",
    )
    session = options.loc[session_index]
    session_key = int(session["session_key"])
    session_type = session.get("session_type")

    drivers = safe_load(load_session_data, Endpoint.DRIVERS, session_key, year)
    info = driver_info(drivers)
    labels = dict(zip(info["driver_number"], info["name_acronym"], strict=True))
    result = safe_load(load_session_data, Endpoint.SESSION_RESULT, session_key, year)
    chosen = sidebar.multiselect(
        "Pilotos",
        list(labels),
        default=[n for n in default_drivers(drivers, result) if n in labels],
        format_func=lambda number: f"{labels[number]} ({number})",
        key=f"drivers_{session_key}",
    )

    selection = Selection(
        year=int(year),
        meeting_key=int(meeting_key),
        meeting_name=names[meeting_key],
        session_key=session_key,
        session_name=str(session["session_name"]),
        session_type=session_type if isinstance(session_type, str) else None,
        driver_numbers=tuple(int(number) for number in chosen),
    )
    st.session_state[SELECTION_KEY] = selection
    return selection


def require_selection() -> Selection:
    """Selection atual; interrompe a página se ainda não houver uma."""
    selection = st.session_state.get(SELECTION_KEY)
    if selection is None:
        st.info(
            "Escolha uma temporada, um Grande Prêmio e uma sessão na barra lateral."
        )
        st.stop()
    return selection


def page_header(title: str, selection: Selection) -> None:
    """Título da página com o contexto selecionado."""
    st.title(title)
    st.caption(
        f"{selection.year} · {selection.meeting_name} · {selection.session_name}"
    )


def session_frame(selection: Selection, endpoint: str) -> pd.DataFrame:
    """Dados de um endpoint para a sessão selecionada (erros viram aviso na tela)."""
    return safe_load(
        load_session_data,
        endpoint,
        selection.session_key,
        selection.year,
        selection.session_type,
    )
