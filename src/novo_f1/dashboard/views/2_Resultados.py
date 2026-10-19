"""Página: classificação, grid x chegada e campeonato."""

import pandas as pd
import streamlit as st

from novo_f1.dashboard.charts import championship_chart, gap_bar, grid_vs_finish_chart
from novo_f1.dashboard.data import load_session_data, load_sessions, safe_load
from novo_f1.dashboard.selection import (
    page_header,
    require_selection,
    session_frame,
)
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.transformation.calendar import grid_session_key
from novo_f1.transformation.results import (
    championship_standings,
    classification,
    grid_vs_finish,
)

selection = require_selection()
page_header("Resultados", selection)


drivers = session_frame(selection, Endpoint.DRIVERS)
result = classification(session_frame(selection, Endpoint.SESSION_RESULT), drivers)

if result.empty:
    st.warning("Resultado ainda não publicado para esta sessão.")
else:
    st.subheader("Classificação")
    if selection.is_race:
        chart_data = result
        value, title = "gap_seconds", "Diferença para o vencedor"
    else:
        chart_data = result.assign(
            delta=result["best_time"] - result["best_time"].min()
        )
        value, title = "delta", "Diferença para o melhor tempo"
    st.plotly_chart(gap_bar(chart_data, value, title))
    st.dataframe(
        result.drop(
            columns=[
                "team_colour",
                "gap_seconds",
                *[q for q in ("q1", "q2", "q3") if result[q].isna().all()],
            ]
        ),
        hide_index=True,
        column_config={
            "position": st.column_config.NumberColumn("Pos.", format="%d"),
            "driver_number": "Nº",
            "name_acronym": "Piloto",
            "full_name": "Nome",
            "team_name": "Equipe",
            "status": "Status",
            "number_of_laps": st.column_config.NumberColumn("Voltas", format="%d"),
            "best_time": st.column_config.NumberColumn("Tempo (s)", format="%.3f"),
            "q1": st.column_config.NumberColumn("Q1", format="%.3f"),
            "q2": st.column_config.NumberColumn("Q2", format="%.3f"),
            "q3": st.column_config.NumberColumn("Q3", format="%.3f"),
            "gap_text": "Gap",
        },
    )

if not selection.is_race:
    st.info("Grid de largada e campeonato existem apenas em sessões de corrida.")
    st.stop()

grid_key = grid_session_key(
    safe_load(load_sessions, selection.year), selection.session_key
)
starting_grid = (
    safe_load(load_session_data, Endpoint.STARTING_GRID, grid_key, selection.year)
    if grid_key is not None
    else pd.DataFrame()
)
grid = grid_vs_finish(
    starting_grid, session_frame(selection, Endpoint.SESSION_RESULT), drivers
)
if grid.empty:
    st.info("Grid de largada indisponível para esta corrida.")
else:
    st.subheader("Grid x chegada")
    st.plotly_chart(grid_vs_finish_chart(grid))

st.subheader("Campeonato após a sessão")
st.warning("Os endpoints de campeonato da OpenF1 estão em beta.", icon="⚠️")
col_drivers, col_teams = st.columns(2)
standings = championship_standings(
    session_frame(selection, Endpoint.CHAMPIONSHIP_DRIVERS), drivers
)
if standings.empty:
    col_drivers.info("Sem dados de campeonato de pilotos.")
else:
    col_drivers.plotly_chart(championship_chart(standings, "name_acronym", "Pilotos"))
teams = championship_standings(
    session_frame(selection, Endpoint.CHAMPIONSHIP_TEAMS), drivers
)
if teams.empty:
    col_teams.info("Sem dados de campeonato de construtores.")
else:
    col_teams.plotly_chart(championship_chart(teams, "team_name", "Construtores"))
