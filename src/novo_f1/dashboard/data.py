"""Wrappers ``st.cache_data`` sobre o repositório (cache em memória + Parquet)."""

from collections.abc import Callable

import httpx
import pandas as pd
import streamlit as st

from novo_f1.services.repository import Repository


@st.cache_resource
def get_repository() -> Repository:
    """Repositório compartilhado pela sessão do Streamlit."""
    return Repository.from_settings()


@st.cache_data(show_spinner="Carregando meetings...")
def load_meetings(year: int) -> pd.DataFrame:
    """Meetings da temporada."""
    return get_repository().meetings(year)


@st.cache_data(show_spinner="Carregando sessões...")
def load_sessions(year: int) -> pd.DataFrame:
    """Sessões da temporada."""
    return get_repository().sessions(year)


@st.cache_data(show_spinner="Carregando dados da sessão...")
def load_session_data(
    endpoint: str, session_key: int, year: int, session_type: str | None = None
) -> pd.DataFrame:
    """Dados de um endpoint por sessão."""
    return get_repository().session_data(endpoint, session_key, year, session_type)


@st.cache_data(show_spinner="Carregando telemetria da volta...")
def load_lap_telemetry(
    endpoint: str,
    session_key: int,
    year: int,
    driver_number: int,
    lap_number: int,
    window: tuple[pd.Timestamp, pd.Timestamp],
) -> pd.DataFrame:
    """Telemetria (``car_data``/``location``) de uma volta."""
    return get_repository().lap_telemetry(
        endpoint, session_key, year, driver_number, lap_number, window
    )


def safe_load[**P](
    loader: Callable[P, pd.DataFrame], *args: P.args, **kwargs: P.kwargs
) -> pd.DataFrame:
    """Executa um loader e mostra o erro na tela em vez de quebrar a página."""
    try:
        return loader(*args, **kwargs)
    except httpx.HTTPError as error:
        st.error(f"Falha ao consultar a OpenF1: {error}")
        return pd.DataFrame()
