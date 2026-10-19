"""Entrada do dashboard Streamlit: barra lateral comum + navegação entre páginas.

Execute com ``poetry run python -m novo_f1.main dashboard``.
"""

from pathlib import Path

import streamlit as st

from novo_f1.dashboard.selection import render_sidebar

# A pasta NÃO pode se chamar "pages": o Streamlit a detecta como multipage
# legado e, ao abrir uma URL de página direto, executa a página sem passar por
# este arquivo (sem barra lateral). As rotas vêm só do st.navigation abaixo.
VIEWS_DIR = Path(__file__).parent / "views"
PAGES = (
    ("1_Calendario.py", "Calendário", ":material/calendar_month:"),
    ("2_Resultados.py", "Resultados", ":material/emoji_events:"),
    ("3_Voltas.py", "Voltas", ":material/timer:"),
    ("4_Estrategia.py", "Estratégia", ":material/tire_repair:"),
    ("5_Telemetria.py", "Telemetria", ":material/speed:"),
)


def main() -> None:
    """Configura a página, desenha a seleção e executa a página escolhida."""
    st.set_page_config(page_title="Novo F1", page_icon="🏎️", layout="wide")
    navigation = st.navigation(
        [
            st.Page(VIEWS_DIR / file, title=title, icon=icon)
            for file, title, icon in PAGES
        ]
    )
    render_sidebar()
    st.sidebar.caption(
        "Dados: [OpenF1](https://openf1.org) — API não oficial, sem vínculo com a F1."
    )
    navigation.run()


main()
