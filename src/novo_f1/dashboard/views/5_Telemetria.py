"""Página: telemetria por volta, traçado, clima e direção de prova."""

import streamlit as st

from novo_f1.dashboard.charts import driver_styles
from novo_f1.dashboard.data import load_lap_telemetry, safe_load
from novo_f1.dashboard.selection import page_header, require_selection, session_frame
from novo_f1.dashboard.telemetry_charts import (
    TelemetryTrace,
    telemetry_chart,
    track_map,
    weather_chart,
)
from novo_f1.ingestion.endpoints import Endpoint
from novo_f1.transformation.common import to_utc
from novo_f1.transformation.context import key_events, weather_series, weather_summary
from novo_f1.transformation.laps import fastest_lap_per_driver
from novo_f1.transformation.results import driver_info
from novo_f1.transformation.telemetry import (
    lap_window,
    merge_car_location,
    prepare_car_data,
)

MAX_COMPARED = 2

selection = require_selection()
page_header("Telemetria e contexto", selection)

drivers = session_frame(selection, Endpoint.DRIVERS)
info = driver_info(drivers).set_index("driver_number")
styles = driver_styles(driver_info(drivers))
laps = session_frame(selection, Endpoint.LAPS)

st.subheader("Telemetria por volta")
compared = list(selection.driver_numbers[:MAX_COMPARED])
if laps.empty or not compared:
    st.info("Escolha ao menos um piloto na barra lateral (até 2 são comparados).")
else:
    fastest = fastest_lap_per_driver(laps, drivers).set_index("driver_number")
    mode = st.radio(
        "Volta", ["Mais rápida de cada piloto", "Mesma volta"], horizontal=True
    )
    lap_choice = None
    if mode == "Mesma volta":
        lap_choice = int(
            st.number_input(
                "Número da volta",
                min_value=1,
                max_value=int(laps["lap_number"].max()),
                value=1,
            )
        )
    st.caption("A telemetria é baixada sob demanda, apenas para a volta escolhida.")

    traces: list[TelemetryTrace] = []
    for number in compared:
        lap_number = lap_choice
        if lap_number is None and number in fastest.index:
            lap_number = int(fastest.loc[number, "lap_number"])
        window = lap_window(laps, number, lap_number) if lap_number else None
        if window is None:
            st.warning(f"Volta indisponível para o piloto {number}.")
            continue
        args = (selection.session_key, selection.year, number, lap_number, window)
        car = prepare_car_data(safe_load(load_lap_telemetry, Endpoint.CAR_DATA, *args))
        location = safe_load(load_lap_telemetry, Endpoint.LOCATION, *args)
        acronym = info["name_acronym"].get(number, str(number))
        colour, dash = styles.get(number, ("#8A8A8A", "solid"))
        traces.append(
            TelemetryTrace(
                f"{acronym} · volta {lap_number}",
                colour,
                dash,
                merge_car_location(car, location),
            )
        )

    traces = [trace for trace in traces if not trace.data.empty]
    if traces:
        st.plotly_chart(telemetry_chart(traces))
        st.plotly_chart(track_map(traces[0].data, traces[0].label))
        drs = traces[0].data["drs_state"].value_counts()
        st.caption("DRS (amostras) — " + ", ".join(f"{k}: {v}" for k, v in drs.items()))
    else:
        st.info("Sem telemetria para a(s) volta(s) escolhida(s).")

st.subheader("Clima")
weather_raw = session_frame(selection, Endpoint.WEATHER)
summary = weather_summary(weather_raw)
if summary["air_min"] is None:
    st.info("Sem dados de clima.")
else:
    col_air, col_track, col_rain = st.columns(3)
    col_air.metric("Ar (°C)", f"{summary['air_min']:.0f}-{summary['air_max']:.0f}")
    col_track.metric(
        "Pista (°C)", f"{summary['track_min']:.0f}-{summary['track_max']:.0f}"
    )
    col_rain.metric("Chuva", "Sim" if summary["rain"] else "Não")
    st.plotly_chart(weather_chart(weather_series(weather_raw)))

st.subheader("Direção de prova")
events = key_events(session_frame(selection, Endpoint.RACE_CONTROL))
if events.empty:
    st.info("Sem bandeiras de pista ou safety car registrados.")
else:
    st.dataframe(
        events[["date", "lap_number", "category", "flag", "message"]],
        hide_index=True,
        column_config={
            "date": st.column_config.DatetimeColumn("Horário (UTC)", format="HH:mm:ss"),
            "lap_number": st.column_config.NumberColumn("Volta", format="%d"),
            "category": "Categoria",
            "flag": "Bandeira",
            "message": "Mensagem",
        },
    )

st.subheader("Rádios da equipe")
st.warning("A OpenF1 publica só uma seleção parcial de rádios.", icon="⚠️")
radio = session_frame(selection, Endpoint.TEAM_RADIO)
if selection.driver_numbers and not radio.empty:
    radio = radio[radio["driver_number"].isin(selection.driver_numbers)]
if radio.empty:
    st.info("Nenhum rádio disponível para os pilotos escolhidos.")
else:
    st.dataframe(
        radio.assign(piloto=radio["driver_number"].map(info["name_acronym"]))[
            ["date", "piloto", "recording_url"]
        ].assign(date=lambda frame: to_utc(frame["date"])),
        hide_index=True,
        column_config={
            "date": st.column_config.DatetimeColumn("Horário (UTC)", format="HH:mm:ss"),
            "recording_url": st.column_config.LinkColumn("Áudio (MP3)"),
        },
    )
