"""Página: calendário da temporada e sessões do Grande Prêmio selecionado."""

import streamlit as st

from novo_f1.dashboard.charts import season_timeline
from novo_f1.dashboard.data import load_meetings, load_sessions, safe_load
from novo_f1.dashboard.selection import page_header, require_selection
from novo_f1.transformation.calendar import meeting_sessions, season_calendar

selection = require_selection()
page_header("Calendário", selection)

calendar = season_calendar(
    safe_load(load_meetings, selection.year), safe_load(load_sessions, selection.year)
)
races = calendar[~calendar["is_testing"]]
col_total, col_sprint, col_cancelled = st.columns(3)
col_total.metric("Grandes Prêmios", len(races))
col_sprint.metric("Com sprint", int(races["has_sprint"].sum()))
col_cancelled.metric("Cancelados", int(races["is_cancelled"].sum()))

st.plotly_chart(season_timeline(calendar))
st.caption("◆ fim de semana com sprint · pontos esmaecidos = cancelados")

st.subheader("Tabela da temporada")
st.dataframe(
    calendar.drop(columns=["meeting_key"]),
    hide_index=True,
    column_config={
        "meeting_name": "Grande Prêmio",
        "country_name": "País",
        "location": "Local",
        "circuit_short_name": "Circuito",
        "circuit_type": "Tipo",
        "date_start": st.column_config.DatetimeColumn("Início", format="DD/MM/YYYY"),
        "date_end": st.column_config.DatetimeColumn("Fim", format="DD/MM/YYYY"),
        "is_cancelled": "Cancelado",
        "is_testing": "Testes",
        "sessions": "Sessões",
        "has_sprint": "Sprint",
    },
)

st.subheader(f"Sessões — {selection.meeting_name}")
sessions = meeting_sessions(
    safe_load(load_sessions, selection.year), selection.meeting_key
)
st.dataframe(
    sessions[["session_name", "session_type", "date_start", "session_key"]],
    hide_index=True,
    column_config={
        "session_name": "Sessão",
        "session_type": "Tipo",
        "date_start": st.column_config.DatetimeColumn(
            "Início (UTC)", format="DD/MM/YYYY HH:mm"
        ),
        "session_key": st.column_config.NumberColumn("session_key", format="%d"),
    },
)
