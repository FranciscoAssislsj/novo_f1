"""Página: stints/pneus, pit stops, posições e gaps ao longo da corrida."""

import streamlit as st

from novo_f1.dashboard.charts import (
    driver_styles,
    gap_chart,
    pit_stop_chart,
    positions_chart,
    stint_gantt,
)
from novo_f1.dashboard.selection import page_header, require_selection, session_frame
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.transformation.common import to_utc
from novo_f1.transformation.positions import gaps_series, position_by_lap
from novo_f1.transformation.results import driver_info, with_driver_info
from novo_f1.transformation.strategy import pit_stop_counts, pit_summary, tyre_timeline

selection = require_selection()
page_header("Estratégia", selection)

drivers = session_frame(selection, Endpoint.DRIVERS)
styles = driver_styles(driver_info(drivers))

st.subheader("Pneus por stint")
timeline = tyre_timeline(session_frame(selection, Endpoint.STINTS), drivers)
if timeline.empty:
    st.info("Sem dados de stints para esta sessão.")
else:
    st.plotly_chart(stint_gantt(timeline))

st.subheader("Pit stops")
stops = pit_summary(session_frame(selection, Endpoint.PIT), drivers)
if stops.empty:
    st.info("Nenhuma passagem pelo pit lane registrada.")
else:
    col_chart, col_table = st.columns([3, 2])
    col_chart.plotly_chart(pit_stop_chart(stops))
    col_table.dataframe(
        pit_stop_counts(stops),
        hide_index=True,
        column_config={
            "name_acronym": "Piloto",
            "stops": "Paradas",
            "best_lane": st.column_config.NumberColumn(
                "Melhor pit lane (s)", format="%.2f"
            ),
            "mean_lane": st.column_config.NumberColumn(
                "Média pit lane (s)", format="%.2f"
            ),
            "best_stop": st.column_config.NumberColumn(
                "Melhor parado (s)", format="%.2f"
            ),
        },
    )
    if stops["stop_duration"].isna().all():
        st.caption(
            "Tempo parado (stop_duration) só existe a partir do GP dos EUA de 2024."
        )

st.subheader("Posições")
positions = position_by_lap(
    session_frame(selection, Endpoint.POSITION), session_frame(selection, Endpoint.LAPS)
)
if positions.empty:
    st.info("Sem dados de posição para esta sessão.")
else:
    show_all = st.toggle("Mostrar todos os pilotos", value=not selection.driver_numbers)
    if not show_all:
        positions = positions[positions["driver_number"].isin(selection.driver_numbers)]
    st.plotly_chart(positions_chart(with_driver_info(positions, drivers), styles))

if not selection.is_race:
    st.info("Gaps e ultrapassagens existem apenas em sessões de corrida.")
    st.stop()

st.subheader("Gap para o líder")
gaps = gaps_series(session_frame(selection, Endpoint.INTERVALS), drivers)
if selection.driver_numbers:
    gaps = gaps[gaps["driver_number"].isin(selection.driver_numbers)]
if gaps.empty:
    st.info("Sem dados de intervalos para os pilotos escolhidos.")
else:
    st.plotly_chart(gap_chart(gaps, styles))
    st.caption("Pilotos com volta de atraso ficam sem gap numérico nesses trechos.")

st.subheader("Ultrapassagens")
st.warning("Dados de ultrapassagens da OpenF1 podem estar incompletos.", icon="⚠️")
overtakes = session_frame(selection, Endpoint.OVERTAKES)
if overtakes.empty:
    st.info("Nenhuma ultrapassagem registrada.")
else:
    names = driver_info(drivers).set_index("driver_number")["name_acronym"]
    st.dataframe(
        overtakes.assign(
            date=to_utc(overtakes["date"]),
            ultrapassou=overtakes["overtaking_driver_number"].map(names),
            ultrapassado=overtakes["overtaken_driver_number"].map(names),
        )[["date", "ultrapassou", "ultrapassado", "position"]],
        hide_index=True,
        column_config={
            "date": st.column_config.DatetimeColumn("Horário (UTC)", format="HH:mm:ss"),
            "ultrapassou": "Ultrapassou",
            "ultrapassado": "Ultrapassado",
            "position": "Nova posição",
        },
    )
