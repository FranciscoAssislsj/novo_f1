"""Builders Plotly de telemetria, traçado e clima."""

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from novo_f1.dashboard.charts import LINE_WIDTH, SERIES_COLOURS, base_layout

TELEMETRY_CHANNELS = (
    ("speed", "Velocidade (km/h)"),
    ("throttle", "Acelerador (%)"),
    ("brake", "Freio"),
    ("n_gear", "Marcha"),
)


@dataclass(frozen=True)
class TelemetryTrace:
    """Uma volta de um piloto a ser desenhada."""

    label: str
    colour: str
    dash: str
    data: pd.DataFrame


def telemetry_chart(traces: list[TelemetryTrace]) -> go.Figure:
    """Painéis empilhados (velocidade, acelerador, freio, marcha) x distância.

    Cada canal tem seu próprio painel e eixo, compartilhando o eixo x, em vez
    de vários eixos y sobrepostos.
    """
    fig = make_subplots(
        rows=len(TELEMETRY_CHANNELS),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=[title for _, title in TELEMETRY_CHANNELS],
        row_heights=[0.4, 0.2, 0.2, 0.2],
    )
    for trace in traces:
        for row, (channel, title) in enumerate(TELEMETRY_CHANNELS, start=1):
            if channel not in trace.data:
                continue
            fig.add_trace(
                go.Scatter(
                    x=trace.data["distance_m"],
                    y=trace.data[channel],
                    mode="lines",
                    name=trace.label,
                    legendgroup=trace.label,
                    showlegend=row == 1,
                    line={
                        "color": trace.colour,
                        "dash": trace.dash,
                        "width": LINE_WIDTH,
                        "shape": "hv" if channel == "n_gear" else "linear",
                    },
                    hovertemplate=(
                        f"<b>{trace.label}</b> %{{x:.0f}} m<br>{title}: "
                        "%{y}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )
    fig.update_xaxes(title="distância na volta (m)", row=len(TELEMETRY_CHANNELS))
    return base_layout(fig, "Telemetria da volta", height=850, hovermode="x unified")


def track_map(telemetry: pd.DataFrame, label: str) -> go.Figure:
    """Traçado (x, y) da volta colorido pela velocidade (escala de um só tom)."""
    data = telemetry.dropna(subset=["x", "y"])
    fig = go.Figure(
        go.Scatter(
            x=data["x"],
            y=data["y"],
            mode="markers",
            marker={
                "size": 6,
                "color": data["speed"],
                # Escala de um só tom começando em azul médio, para que os trechos
                # lentos continuem visíveis sobre fundo claro.
                "colorscale": [[0, "#9CC3F0"], [1, "#08306B"]],
                "colorbar": {"title": "km/h"},
                "showscale": True,
            },
            customdata=data[["speed", "n_gear"]] if "n_gear" in data else None,
            hovertemplate=(
                "%{customdata[0]} km/h · marcha %{customdata[1]}<extra></extra>"
            ),
            name=label,
            showlegend=False,
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return base_layout(fig, f"Traçado — {label}", height=550)


def weather_chart(weather: pd.DataFrame) -> go.Figure:
    """Temperaturas (°C) e umidade (%) em painéis separados; chuva marcada."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Temperatura (°C)", "Umidade (%)"),
        row_heights=[0.65, 0.35],
    )
    for colour, (column, name) in zip(
        SERIES_COLOURS,
        (("air_temperature", "Ar"), ("track_temperature", "Pista")),
        strict=True,
    ):
        fig.add_trace(
            go.Scatter(
                x=weather["date"],
                y=weather[column],
                mode="lines",
                name=name,
                line={"color": colour, "width": LINE_WIDTH},
                hovertemplate=f"{name}: %{{y:.1f}} °C<extra></extra>",
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=weather["date"],
            y=weather["humidity"],
            mode="lines",
            name="Umidade",
            line={"color": SERIES_COLOURS[0], "width": LINE_WIDTH},
            hovertemplate="%{y:.0f}%<extra></extra>",
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    rain = weather[weather["rainfall"]]
    if not rain.empty:
        fig.add_trace(
            go.Scatter(
                x=rain["date"],
                y=rain["humidity"],
                mode="markers",
                name="Chuva",
                marker={"symbol": "triangle-down", "size": 9, "color": "#0067AD"},
                hovertemplate="Chuva<extra></extra>",
            ),
            row=2,
            col=1,
        )
    fig.update_xaxes(title="horário (UTC)", row=2)
    return base_layout(fig, "Clima da sessão", height=500, hovermode="x unified")
