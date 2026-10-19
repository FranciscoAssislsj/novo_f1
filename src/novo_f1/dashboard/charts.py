"""Builders Plotly puros: recebem DataFrames e devolvem `go.Figure`.

Convenções visuais: a cor segue a entidade (cor oficial da equipe ou do
composto), companheiros de equipe são diferenciados pelo traço (sólido x
tracejado), linhas de 2px, um único eixo y por gráfico e hover em todas as
marcas.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from novo_f1.transformation.strategy import COMPOUND_COLOURS

LINE_WIDTH = 2
MARKER_SIZE = 8
SERIES_COLOURS = ("#2A78D6", "#EB6834")
"""Slots categóricos 1 e 2 para séries sem cor de domínio."""
NEUTRAL_COLOUR = "#8A8A8A"
MARK_OUTLINE = "rgba(60, 60, 60, 0.55)"


def base_layout(fig: go.Figure, title: str, **layout: object) -> go.Figure:
    """Aplica o layout padrão (título, margens, legenda no topo, hover).

    Chaves passadas em ``layout`` sobrescrevem os padrões.
    """
    defaults: dict[str, object] = {
        "hovermode": "closest",
        "margin": {"l": 10, "r": 10, "t": 90, "b": 10},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    }
    # Título no topo do contêiner e legenda logo acima da área do gráfico, na
    # faixa da margem superior, para que os dois não se sobreponham.
    title_layout = {
        "text": title,
        "x": 0,
        "xanchor": "left",
        "y": 1,
        "yref": "container",
        "yanchor": "top",
        "pad": {"t": 8},
    }
    fig.update_layout(title=title_layout, **(defaults | layout))
    return fig


def driver_styles(drivers: pd.DataFrame) -> dict[int, tuple[str, str]]:
    """Cor e traço por piloto: o 2º piloto de cada equipe usa traço tracejado.

    Args:
        drivers: Saída de `driver_info` (``driver_number``, ``team_name``,
            ``team_colour``).

    Returns:
        ``{driver_number: (cor, dash)}``.
    """
    styles: dict[int, tuple[str, str]] = {}
    seen: dict[object, int] = {}
    for row in drivers.sort_values("driver_number").itertuples(index=False):
        team = row.team_name if isinstance(row.team_name, str) else row.driver_number
        dash = "solid" if seen.get(team, 0) == 0 else "dash"
        seen[team] = seen.get(team, 0) + 1
        styles[int(row.driver_number)] = (row.team_colour, dash)
    return styles


def season_timeline(calendar: pd.DataFrame) -> go.Figure:
    """Linha do tempo da temporada (um ponto por meeting; losango = sprint)."""
    fig = go.Figure()
    if not calendar.empty:
        status = calendar["is_cancelled"].map({True: "Cancelado", False: "Realizado"})
        fig.add_trace(
            go.Scatter(
                x=calendar["date_start"],
                y=calendar["meeting_name"],
                mode="markers",
                marker={
                    "size": 12,
                    "color": SERIES_COLOURS[0],
                    "symbol": [
                        "diamond" if sprint else "circle"
                        for sprint in calendar["has_sprint"]
                    ],
                    "opacity": [0.35 if c else 1 for c in calendar["is_cancelled"]],
                },
                customdata=pd.concat(
                    [calendar["circuit_short_name"], status], axis=1
                ).to_numpy(),
                hovertemplate=(
                    "<b>%{y}</b><br>%{x|%d/%m/%Y}<br>%{customdata[0]}"
                    "<br>%{customdata[1]}<extra></extra>"
                ),
                name="Meetings",
                showlegend=False,
            )
        )
    fig.update_yaxes(autorange="reversed", title=None)
    return base_layout(
        fig, "Calendário da temporada", height=max(400, 26 * len(calendar))
    )


def gap_bar(frame: pd.DataFrame, value_column: str, title: str) -> go.Figure:
    """Barras horizontais de diferença (s) por piloto, na cor da equipe."""
    data = frame.dropna(subset=[value_column])
    fig = go.Figure(
        go.Bar(
            x=data[value_column],
            y=data["name_acronym"],
            orientation="h",
            marker={
                "color": data["team_colour"],
                "line": {"color": MARK_OUTLINE, "width": 1},
            },
            hovertemplate="<b>%{y}</b><br>%{x:.3f}s<extra></extra>",
            name=title,
        )
    )
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title="segundos")
    return base_layout(fig, title, height=max(350, 24 * len(data)), bargap=0.25)


def grid_vs_finish_chart(frame: pd.DataFrame) -> go.Figure:
    """Halteres de posição de largada → chegada por piloto."""
    fig = go.Figure()
    data = frame.dropna(subset=["grid", "finish"])
    for row in data.itertuples(index=False):
        fig.add_trace(
            go.Scatter(
                x=[row.grid, row.finish],
                y=[row.name_acronym, row.name_acronym],
                mode="lines+markers",
                line={"color": row.team_colour, "width": LINE_WIDTH},
                marker={
                    "size": [MARKER_SIZE, MARKER_SIZE + 4],
                    "symbol": ["circle-open", "circle"],
                    "color": row.team_colour,
                    "line": {"color": MARK_OUTLINE, "width": 1},
                },
                hovertemplate=(
                    f"<b>{row.name_acronym}</b><br>Largada P{int(row.grid)} → "
                    f"Chegada P{int(row.finish)}<extra></extra>"
                ),
                showlegend=False,
            )
        )
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title="posição (○ largada, ● chegada)", dtick=1)
    return base_layout(fig, "Grid x chegada", height=max(400, 24 * len(data)))


def championship_chart(
    standings: pd.DataFrame, label_column: str, title: str
) -> go.Figure:
    """Pontos atuais no campeonato (barras horizontais)."""
    colour = standings.get(
        "team_colour", pd.Series(NEUTRAL_COLOUR, index=standings.index)
    )
    fig = go.Figure(
        go.Bar(
            x=standings["points_current"],
            y=standings[label_column],
            orientation="h",
            marker={"color": colour.fillna(NEUTRAL_COLOUR)},
            customdata=standings["points_gained"],
            hovertemplate=(
                "<b>%{y}</b><br>%{x} pts (+%{customdata} nesta sessão)<extra></extra>"
            ),
            text=standings["points_current"],
            textposition="outside",
            name=title,
        )
    )
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title="pontos")
    return base_layout(fig, title, height=max(400, 24 * len(standings)))


def lap_times_chart(
    laps: pd.DataFrame, styles: dict[int, tuple[str, str]]
) -> go.Figure:
    """Tempo de volta (s) por número da volta, uma linha por piloto."""
    fig = go.Figure()
    for driver, group in laps.sort_values("lap_number").groupby("driver_number"):
        colour, dash = styles.get(int(driver), (NEUTRAL_COLOUR, "solid"))
        name = group["name_acronym"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=group["lap_number"],
                y=group["lap_duration"],
                mode="lines+markers",
                name=name,
                line={"color": colour, "dash": dash, "width": LINE_WIDTH},
                marker={"size": 5},
                hovertemplate=(
                    f"<b>{name}</b> volta %{{x}}<br>%{{y:.3f}}s<extra></extra>"
                ),
            )
        )
    fig.update_xaxes(title="volta")
    fig.update_yaxes(title="tempo de volta (s)")
    return base_layout(fig, "Tempos de volta", hovermode="x unified")


def sector_chart(sectors: pd.DataFrame) -> go.Figure:
    """Diferença para o melhor tempo de cada setor (um painel por setor)."""
    fig = make_subplots(
        rows=1,
        cols=3,
        shared_yaxes=True,
        subplot_titles=("Setor 1", "Setor 2", "Setor 3"),
    )
    for index in range(3):
        column = f"duration_sector_{index + 1}"
        delta = sectors[column] - sectors[column].min()
        fig.add_trace(
            go.Bar(
                x=delta,
                y=sectors["name_acronym"],
                orientation="h",
                marker={"color": sectors["team_colour"]},
                customdata=sectors[column],
                hovertemplate=(
                    "<b>%{y}</b><br>%{customdata:.3f}s (+%{x:.3f}s)<extra></extra>"
                ),
                showlegend=False,
            ),
            row=1,
            col=index + 1,
        )
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title="+s do melhor")
    return base_layout(fig, "Melhores setores", height=max(400, 22 * len(sectors)))


def stint_gantt(timeline: pd.DataFrame) -> go.Figure:
    """Gantt de stints: uma barra por stint, colorida pelo composto."""
    fig = go.Figure()
    for compound, group in timeline.groupby("compound", sort=False):
        fig.add_trace(
            go.Bar(
                x=group["laps"],
                base=group["lap_start"] - 1,
                y=group["name_acronym"],
                orientation="h",
                name=str(compound).title(),
                marker={
                    "color": COMPOUND_COLOURS.get(str(compound), NEUTRAL_COLOUR),
                    "line": {"color": MARK_OUTLINE, "width": 1},
                },
                customdata=group[["lap_start", "lap_end", "tyre_age_at_start"]],
                hovertemplate=(
                    "<b>%{y}</b> " + str(compound).title() + "<br>voltas "
                    "%{customdata[0]}-%{customdata[1]}<br>idade inicial "
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title="volta")
    return base_layout(
        fig,
        "Estratégia de pneus",
        barmode="overlay",
        bargap=0.3,
        height=max(400, 24 * timeline["name_acronym"].nunique()),
    )


def pit_stop_chart(pit_stops: pd.DataFrame) -> go.Figure:
    """Tempo no pit lane por volta da parada, um ponto por parada."""
    data = pit_stops.dropna(subset=["lane_duration"])
    fig = go.Figure(
        go.Scatter(
            x=data["lap_number"],
            y=data["lane_duration"],
            mode="markers+text",
            text=data["name_acronym"],
            textposition="top center",
            marker={
                "size": MARKER_SIZE + 4,
                "color": data["team_colour"],
                "line": {"color": MARK_OUTLINE, "width": 1},
            },
            customdata=data["stop_duration"],
            hovertemplate=(
                "<b>%{text}</b> volta %{x}<br>pit lane %{y:.2f}s"
                "<br>parado %{customdata:.2f}s<extra></extra>"
            ),
            showlegend=False,
        )
    )
    fig.update_xaxes(title="volta")
    fig.update_yaxes(title="tempo no pit lane (s)")
    return base_layout(fig, "Pit stops")


def positions_chart(
    positions: pd.DataFrame, styles: dict[int, tuple[str, str]]
) -> go.Figure:
    """Posição por volta (P1 no topo), uma linha por piloto."""
    fig = go.Figure()
    for driver, group in positions.sort_values("lap_number").groupby("driver_number"):
        colour, dash = styles.get(int(driver), (NEUTRAL_COLOUR, "solid"))
        name = group["name_acronym"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=group["lap_number"],
                y=group["position"],
                mode="lines",
                name=name,
                line={
                    "color": colour,
                    "dash": dash,
                    "width": LINE_WIDTH,
                    "shape": "hv",
                },
                hovertemplate=f"<b>{name}</b> volta %{{x}}: P%{{y}}<extra></extra>",
            )
        )
    fig.update_yaxes(autorange="reversed", dtick=1, title="posição")
    fig.update_xaxes(title="volta (0 = grid)")
    return base_layout(fig, "Posições ao longo da corrida", height=600)


def gap_chart(gaps: pd.DataFrame, styles: dict[int, tuple[str, str]]) -> go.Figure:
    """Gap para o líder (s) ao longo do tempo; carros com volta de atraso somem."""
    fig = go.Figure()
    for driver, group in gaps.groupby("driver_number"):
        colour, dash = styles.get(int(driver), (NEUTRAL_COLOUR, "solid"))
        name = group["name_acronym"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=group["gap_to_leader"],
                mode="lines",
                name=name,
                line={"color": colour, "dash": dash, "width": LINE_WIDTH},
                hovertemplate=f"<b>{name}</b><br>+%{{y:.3f}}s<extra></extra>",
            )
        )
    fig.update_yaxes(autorange="reversed", title="gap para o líder (s)")
    fig.update_xaxes(title="horário (UTC)")
    return base_layout(fig, "Gap para o líder", height=500)
