"""Montagem de query strings no formato de filtros da OpenF1.

A OpenF1 usa operadores no próprio nome do parâmetro (``speed>=315``). Em
``params`` o ``httpx`` codificaria a chave ``speed>=`` como ``speed%3E%3D=315``,
quebrando o operador; por isso a query é montada aqui, à mão. Na transmissão o
``httpx`` ainda percent-encoda ``<``/``>`` (``%3C``/``%3E``), forma que a API
aceita normalmente.
"""

import re
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from urllib.parse import quote

type Scalar = str | int | float | bool | date | datetime
type FilterValue = Scalar | Iterable[Scalar] | None

OPERATORS = (">=", "<=", ">", "<", "=")
_KEY_PATTERN = re.compile(r"^(?P<field>[a-z0-9_]+)(?P<op>>=|<=|>|<|=)?$")
_SAFE_CHARS = ":-._~"


def format_value(value: Scalar) -> str:
    """Converte um valor escalar no texto usado pela API.

    Args:
        value: Valor do filtro.

    Returns:
        Representação textual (booleanos em minúsculas, datas em ISO 8601).
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date | datetime):
        return value.isoformat()
    return str(value)


def _split_key(key: str) -> tuple[str, str]:
    match = _KEY_PATTERN.match(key)
    if match is None:
        raise ValueError(f"Filtro inválido: {key!r}")
    return match["field"], match["op"] or "="


def _as_values(value: FilterValue) -> list[Scalar]:
    if value is None:
        return []
    if isinstance(value, str | bytes | date | datetime | int | float | bool):
        return [value]  # type: ignore[list-item]
    return list(value)


def build_query(filters: Mapping[str, FilterValue]) -> str:
    """Monta a query string a partir de um mapeamento de filtros.

    A chave pode trazer o operador no final (``"date>="``, ``"speed>"``); sem
    operador, usa-se igualdade. Listas geram parâmetros repetidos e ``None`` é
    ignorado.

    Args:
        filters: Mapeamento ``campo[operador] -> valor``.

    Returns:
        Query string sem o ``?`` inicial.

    Raises:
        ValueError: Se uma chave não seguir o formato ``campo[operador]``.

    Example:
        >>> build_query({"session_key": 9161, "speed>=": 315})
        'session_key=9161&speed>=315'
    """
    parts: list[str] = []
    for key, value in filters.items():
        field, operator = _split_key(key)
        for item in _as_values(value):
            encoded = quote(format_value(item), safe=_SAFE_CHARS)
            parts.append(f"{field}{operator}{encoded}")
    return "&".join(parts)
