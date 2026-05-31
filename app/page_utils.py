# -*- coding: utf-8 -*-
"""Utilidades compartidas: setup de paginas, pestañas perezosas y cache de graficos."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.data_loader import load_aggregates
from app.filters import render_sidebar
from app.nav import render_section_nav
from app.narrative import render_apertura
from app.text_es import STORY


def setup_page(etapa_key: str) -> dict[str, Any] | None:
    """Configura pagina, sidebar con progreso y datos filtrados."""
    story = STORY[etapa_key]
    st.set_page_config(
        page_title=story["titulo_menu"],
        layout="wide",
        initial_sidebar_state="expanded",
    )
    aggs = load_aggregates()
    _, data = render_sidebar(aggs, etapa=story["etapa"], section_id=etapa_key)
    render_section_nav(etapa_key)
    render_apertura(etapa_key, data)
    if data["casos"] == 0:
        st.warning(
            "No hay casos con la selección actual. Amplíe el periodo o el departamento."
        )
        st.stop()
    return data


def lazy_tab(options: list[str], key: str) -> str:
    """Selector de pestaña: solo renderiza el contenido de la vista activa."""
    return st.radio(
        "Vista",
        options,
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )


def _df_payload(df: pd.DataFrame) -> str:
    return df.to_json(orient="split", date_format="iso")


@st.cache_data(show_spinner=False)
def cached_figure(
    chart_id: str,
    cache_key: tuple,
    payload: str,
    extra: str = "",
    chart_height: int | None = None,
    _figures_v: int = 4,
) -> str:
    """Construye figura Plotly una vez por combinacion filtro + vista."""
    from app import charts

    df = pd.read_json(StringIO(payload), orient="split")
    builders: dict[str, Callable[..., go.Figure]] = {
        "linea_anual": charts.linea_anual,
        "linea_anual_pct": charts.linea_anual_pct,
        "dept_top10": lambda d: charts.barras_horizontales(
            d,
            "departamento_hecho",
            title="Departamentos con más casos registrados",
            pct_col="pct",
        ),
        "zona": charts.barras_zona_pct,
        "edad_sexo": charts.barras_apiladas_pct,
        "heatmap_dh": charts.heatmap_dia_hora,
        "top_franjas": charts.barras_top_franjas,
        "mecanismos": lambda d: charts.barras_horizontales(
            d, "categoria", title="Mecanismos de lesión más frecuentes", pct_col="pct"
        ),
        "escenarios": charts.barras_escenarios,
        "severidad": charts.barras_severidad,
        "agresores": lambda d: charts.barras_horizontales(
            d,
            "categoria",
            title="Presunto agresor más frecuente",
            pct_col="pct",
            height=chart_height,
        ),
        "resumen_perfil": charts.barras_perfil_seleccion,
    }
    builder = builders.get(chart_id)
    if builder is None:
        raise ValueError(f"Grafico no registrado: {chart_id}")
    if chart_id == "severidad":
        fig = charts.barras_severidad(df, height=chart_height)
    else:
        fig = builder(df)
    if chart_height is not None and chart_id not in ("severidad", "agresores"):
        fig.update_layout(height=chart_height)
    return fig.to_json()


def _chart_ayuda_alineada(texto: str) -> None:
    """Bloque de ayuda con altura fija para alinear gráficas en columnas."""
    st.markdown(
        f'<div style="min-height:4.5rem;display:flex;align-items:flex-end;'
        f'margin-bottom:0.25rem;font-size:0.875rem;color:#64748b;line-height:1.45;">'
        f"{texto}</div>",
        unsafe_allow_html=True,
    )


def show_cached_chart(
    fig_json: str,
    chart_key: str,
    ayuda: str | None = None,
    *,
    ayuda_alineada: bool = False,
) -> None:
    from app.theme import PLOTLY_CONFIG

    if ayuda:
        if ayuda_alineada:
            _chart_ayuda_alineada(ayuda)
        else:
            st.caption(ayuda)

    fig = go.Figure(json.loads(fig_json))
    st.plotly_chart(fig, use_container_width=True, key=chart_key, config=PLOTLY_CONFIG)


# Registrar ciclo por separado (firma distinta)
@st.cache_data(show_spinner=False)
def cached_ciclo_figure(
    cache_key: tuple, payload: str, sexo: str, _figures_v: int = 4
) -> str:
    from app.charts import barras_ciclo

    df = pd.read_json(StringIO(payload), orient="split")
    return barras_ciclo(df, sexo_resaltar=sexo).to_json()


@st.cache_data(show_spinner=False)
def cached_muni_figure(
    cache_key: tuple,
    payload: str,
    departamento: str,
    *,
    label_col: str = "municipio_hecho",
    title: str | None = None,
) -> str:
    from app.charts import barras_municipios

    df = pd.read_json(StringIO(payload), orient="split")
    chart_title = title or f"Top 5 municipios en {departamento}"
    return barras_municipios(df, title=chart_title, label_col=label_col).to_json()


@st.cache_data(show_spinner="Cargando mapa de Colombia...")
def load_colombia_geojson() -> dict:
    import requests

    url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/3aadedf47badbdac823b00dbe259f6bc6d9e1899/colombia.geo.json"
    return requests.get(url, timeout=10).json()
