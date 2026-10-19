"""Pilotos, classificação, grid x chegada e campeonato."""

from typing import Any

import pandas as pd

from novo_f1.transformation.common import (
    as_list,
    normalize_colour,
    require_columns,
    to_float,
)

DRIVER_COLUMNS = [
    "driver_number",
    "name_acronym",
    "full_name",
    "broadcast_name",
    "team_name",
    "team_colour",
    "headshot_url",
]

CLASSIFICATION_COLUMNS = [
    "position",
    "driver_number",
    "name_acronym",
    "full_name",
    "team_name",
    "team_colour",
    "status",
    "number_of_laps",
    "best_time",
    "q1",
    "q2",
    "q3",
    "gap_seconds",
    "gap_text",
]


def driver_info(drivers: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por piloto, com cor da equipe em ``#RRGGBB``.

    O campo depreciado ``country_code`` é descartado.
    """
    if not require_columns(drivers, "driver_number"):
        return pd.DataFrame(columns=DRIVER_COLUMNS)
    info = drivers.drop_duplicates("driver_number", keep="last").copy()
    for column in DRIVER_COLUMNS:
        if column not in info:
            info[column] = pd.NA
    info["driver_number"] = info["driver_number"].astype(int)
    info["team_colour"] = info["team_colour"].map(normalize_colour)
    info["name_acronym"] = info["name_acronym"].fillna(
        info["driver_number"].astype(str)
    )
    return info[DRIVER_COLUMNS].sort_values("driver_number").reset_index(drop=True)


def with_driver_info(frame: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Anexa sigla, nome, equipe e cor ao DataFrame por ``driver_number``."""
    info = driver_info(drivers)
    result = frame.copy()
    result["driver_number"] = result["driver_number"].astype(int)
    merged = result.merge(info, on="driver_number", how="left", suffixes=("", "_d"))
    merged["name_acronym"] = merged["name_acronym"].fillna(
        merged["driver_number"].astype(str)
    )
    merged["team_colour"] = merged["team_colour"].fillna(normalize_colour(None))
    return merged


def result_status(row: pd.Series) -> str:
    """Status textual de uma linha de ``session_result``."""
    for flag, label in (("dsq", "DSQ"), ("dns", "DNS"), ("dnf", "DNF")):
        if bool(row.get(flag)) and not pd.isna(row.get(flag)):
            return label
    return "Classificado"


def _last_valid(values: list[Any] | None) -> Any:
    if not values:
        return None
    valid = [value for value in values if to_float(value) is not None]
    return valid[-1] if valid else None


def split_duration(value: Any) -> dict[str, float | None]:
    """Separa ``duration`` em melhor tempo e Q1-Q3 (quando for array).

    Na classificação o campo é um array ``[Q1, Q2, Q3]``; nas demais sessões é
    um número (melhor volta ou tempo total).
    """
    phases = as_list(value)
    if phases is None:
        return {"best_time": to_float(value), "q1": None, "q2": None, "q3": None}
    padded = [to_float(item) for item in [*phases, None, None, None][:3]]
    return {
        "best_time": to_float(_last_valid(phases)),
        "q1": padded[0],
        "q2": padded[1],
        "q3": padded[2],
    }


def parse_gap(value: Any) -> tuple[float | None, str]:
    """Interpreta ``gap_to_leader``/``interval``.

    Returns:
        ``(segundos, texto)``. Para ``"+1 LAP"`` os segundos são ``None``; para o
        líder (``None``/0) o texto é vazio. Arrays usam o último valor válido.
    """
    phases = as_list(value)
    if phases is not None:
        value = _last_valid(phases)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, ""
    seconds = to_float(value)
    if seconds is not None:
        return seconds, "" if seconds == 0 else f"+{seconds:.3f}s"
    return None, str(value).strip()


def classification(session_result: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    """Classificação final da sessão.

    Args:
        session_result: DataFrame do endpoint ``session_result``.
        drivers: DataFrame do endpoint ``drivers``.

    Returns:
        DataFrame com as colunas de `CLASSIFICATION_COLUMNS`, ordenado por
        posição (não classificados ao final).
    """
    if not require_columns(session_result, "driver_number"):
        return pd.DataFrame(columns=CLASSIFICATION_COLUMNS)
    result = with_driver_info(session_result, drivers)
    durations = pd.DataFrame(
        [split_duration(value) for value in result.get("duration", pd.Series())],
        index=result.index,
        columns=["best_time", "q1", "q2", "q3"],
    )
    gaps = [parse_gap(value) for value in result.get("gap_to_leader", pd.Series())]
    result = result.assign(
        best_time=durations["best_time"],
        q1=durations["q1"],
        q2=durations["q2"],
        q3=durations["q3"],
        gap_seconds=[gap[0] for gap in gaps] or None,
        gap_text=[gap[1] for gap in gaps] or "",
        status=result.apply(result_status, axis=1),
        position=pd.to_numeric(result.get("position"), errors="coerce"),
        number_of_laps=pd.to_numeric(result.get("number_of_laps"), errors="coerce"),
    )
    result = result.sort_values("position", na_position="last")
    return result[CLASSIFICATION_COLUMNS].reset_index(drop=True)


def grid_vs_finish(
    starting_grid: pd.DataFrame, session_result: pd.DataFrame, drivers: pd.DataFrame
) -> pd.DataFrame:
    """Posição de largada x chegada, com posições ganhas.

    Returns:
        Colunas ``driver_number, name_acronym, team_colour, grid, finish,
        positions_gained`` ordenadas pela chegada.
    """
    columns = [
        "driver_number",
        "name_acronym",
        "team_name",
        "team_colour",
        "grid",
        "finish",
        "positions_gained",
    ]
    if not (
        require_columns(starting_grid, "driver_number", "position")
        and require_columns(session_result, "driver_number", "position")
    ):
        return pd.DataFrame(columns=columns)
    grid = starting_grid[["driver_number", "position"]].rename(
        columns={"position": "grid"}
    )
    finish = session_result[["driver_number", "position"]].rename(
        columns={"position": "finish"}
    )
    merged = grid.merge(finish, on="driver_number", how="outer")
    merged = with_driver_info(merged, drivers)
    merged["grid"] = pd.to_numeric(merged["grid"], errors="coerce")
    merged["finish"] = pd.to_numeric(merged["finish"], errors="coerce")
    merged["positions_gained"] = merged["grid"] - merged["finish"]
    merged = merged.sort_values(["finish", "grid"], na_position="last")
    return merged[columns].reset_index(drop=True)


def championship_standings(
    championship: pd.DataFrame, drivers: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Classificação do campeonato após a sessão (pilotos ou construtores).

    Args:
        championship: ``championship_drivers`` ou ``championship_teams``.
        drivers: Pilotos da sessão, para anexar nome e cor (nos construtores,
            só a cor da equipe).

    Returns:
        DataFrame ordenado por ``position_current`` com ``points_gained``.
    """
    if not require_columns(championship, "position_current", "points_current"):
        return pd.DataFrame()
    standings = championship.copy()
    if "driver_number" in standings and drivers is not None:
        standings = with_driver_info(standings, drivers)
    elif "team_name" in standings and drivers is not None:
        colours = driver_info(drivers).drop_duplicates("team_name")
        colours = colours.set_index("team_name")["team_colour"]
        standings["team_colour"] = standings["team_name"].map(colours)
    standings["points_gained"] = standings["points_current"] - standings.get(
        "points_start", standings["points_current"]
    ).fillna(0)
    return standings.sort_values("position_current").reset_index(drop=True)
