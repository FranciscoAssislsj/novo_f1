"""Smoke test do dashboard: todas as páginas rodam sem exceção, sem rede."""

from datetime import timedelta

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from novo_f1.dashboard import data
from novo_f1.main import DASHBOARD_APP
from novo_f1.services.repository import Repository
from novo_f1.storage.parquet_store import ParquetStore

PAGES = [
    "views/1_Calendario.py",
    "views/2_Resultados.py",
    "views/3_Voltas.py",
    "views/4_Estrategia.py",
    "views/5_Telemetria.py",
]


@pytest.fixture
def app(mocker, payloads, tmp_path):
    payloads["session_result"] = payloads["session_result_race"]
    client = mocker.Mock()
    client.get.side_effect = lambda endpoint, filters: payloads.get(str(endpoint), [])
    repository = Repository(client, ParquetStore(tmp_path), timedelta(hours=24))
    mocker.patch.object(data.Repository, "from_settings", return_value=repository)
    st.cache_data.clear()
    st.cache_resource.clear()
    test = AppTest.from_file(str(DASHBOARD_APP), default_timeout=60)
    test.run()
    return test


def test_sidebar_defaults_to_latest_race(app):
    assert not app.exception
    assert app.sidebar.selectbox(key="meeting").value == 1219
    assert app.sidebar.multiselect(key="drivers_9161").value == [16, 1, 11]


@pytest.mark.parametrize("page", PAGES)
def test_pages_render_without_exceptions(app, page):
    app.switch_page(page)
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert not app.error, [error.value for error in app.error]
    assert app.title[0].value
    assert app.get("plotly_chart") or app.dataframe


def test_results_page_shows_grid_from_qualifying(app):
    app.switch_page("views/2_Resultados.py")
    app.run()

    assert "Grid x chegada" in [header.value for header in app.subheader]


def test_no_legacy_pages_directory():
    # Uma pasta "pages/" faria o Streamlit rotear páginas sem passar pelo app.py.
    assert not (DASHBOARD_APP.parent / "pages").exists()
