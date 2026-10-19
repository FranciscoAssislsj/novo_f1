"""Página: tempos por volta, comparação de pilotos, setores e ritmo por stint."""

import streamlit as st

from novo_f1.dashboard.charts import driver_styles, lap_times_chart, sector_chart
from novo_f1.dashboard.selection import page_header, require_selection, session_frame
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.transformation.laps import (
    best_sectors,
    clean_laps,
    fastest_lap_per_driver,
    remove_outliers,
    stint_pace,
)
from novo_f1.transformation.results import driver_info, with_driver_info

selection = require_selection()
page_header("Voltas", selection)

drivers = session_frame(selection, Endpoint.DRIVERS)
laps = session_frame(selection, Endpoint.LAPS)
if laps.empty:
    st.warning("Sem dados de voltas para esta sessão.")
    st.stop()

fastest = fastest_lap_per_driver(laps, drivers)
if not fastest.empty:
    leader = fastest.iloc[0]
    st.metric(
        f"Volta mais rápida — {leader['name_acronym']}, "
        f"volta {int(leader['lap_number'])}",
        f"{leader['lap_duration']:.3f}s",
    )

st.subheader("Comparação de pilotos")
if not selection.driver_numbers:
    st.info("Escolha pilotos na barra lateral para comparar os tempos de volta.")
else:
    hide_slow = st.toggle(
        "Ocultar voltas atípicas (safety car, tráfego: > 107% da mediana)", value=True
    )
    chosen = clean_laps(laps[laps["driver_number"].isin(selection.driver_numbers)])
    if hide_slow:
        chosen = remove_outliers(chosen)
    styles = driver_styles(driver_info(drivers))
    st.plotly_chart(lap_times_chart(with_driver_info(chosen, drivers), styles))
    st.caption("Voltas de saída dos boxes e voltas sem tempo foram removidas.")

col_fast, col_sectors = st.columns(2)
col_fast.subheader("Melhor volta por piloto")
col_fast.dataframe(
    fastest[["name_acronym", "team_name", "lap_number", "lap_duration", "delta"]],
    hide_index=True,
    column_config={
        "name_acronym": "Piloto",
        "team_name": "Equipe",
        "lap_number": "Volta",
        "lap_duration": st.column_config.NumberColumn("Tempo (s)", format="%.3f"),
        "delta": st.column_config.NumberColumn("Δ (s)", format="+%.3f"),
    },
)
sectors = best_sectors(laps, drivers)
with col_sectors:
    st.subheader("Melhores setores")
    if sectors.empty:
        st.info("Sem tempos de setor.")
    else:
        st.plotly_chart(sector_chart(sectors))

st.subheader("Ritmo por stint")
pace = stint_pace(laps, session_frame(selection, Endpoint.STINTS), drivers)
if selection.driver_numbers:
    pace = pace[pace["driver_number"].isin(selection.driver_numbers)]
st.dataframe(
    pace.drop(columns=["driver_number"]),
    hide_index=True,
    column_config={
        "name_acronym": "Piloto",
        "stint_number": "Stint",
        "compound": "Composto",
        "laps": "Voltas válidas",
        "mean_lap": st.column_config.NumberColumn("Média (s)", format="%.3f"),
        "median_lap": st.column_config.NumberColumn("Mediana (s)", format="%.3f"),
        "best_lap": st.column_config.NumberColumn("Melhor (s)", format="%.3f"),
    },
)
