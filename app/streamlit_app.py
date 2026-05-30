# -*- coding: utf-8 -*-
"""Dashboard: página de inicio con resumen integrado de la selección filtrada."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.analytics import resumen_perfil_seleccion
from app.data_loader import load_aggregates
from app.filters import render_sidebar
from app.kpi import render_kpi_row
from app.nav import render_section_nav
from app.page_utils import _df_payload, cached_figure, show_cached_chart
from app.text_es import UI, chart_ayuda

st.set_page_config(
    page_title=UI["app_title"],
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    with st.spinner("Cargando datos..."):
        aggs = load_aggregates()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

_, data = render_sidebar(aggs, section_id="inicio")

render_section_nav("inicio")

st.title(UI["app_title"])
st.caption("Colombia, 2015–2024 · Casos registrados en valoración medicolegal")
st.markdown(f"**Fuente:** [{UI['source_title']}]({UI['source_url']})")
st.info(UI["disclaimer"])

st.divider()

render_kpi_row(
    [
        ("Total nacional (2015–2024)", f"{aggs.total_nacional:,}"),
        ("Casos en la selección", f"{data['casos']:,}"),
        ("Participación del total", f"{data['pct_total']:.1f}%"),
    ]
)

st.subheader(UI["inicio_resumen_titulo"])
st.caption(UI["inicio_resumen_caption"])

if data["casos"] == 0:
    st.warning("No hay casos con la selección actual. Amplíe el periodo o relaje los filtros del panel lateral.")
else:
    resumen = resumen_perfil_seleccion(data)
    col_tabla, col_graf = st.columns([1.05, 0.95], gap="large")

    with col_tabla:
        st.dataframe(
            resumen,
            column_config={
                "dimension": st.column_config.TextColumn("Dimensión", width="medium"),
                "detalle": st.column_config.TextColumn("Valor destacado", width="large"),
                "casos": st.column_config.NumberColumn("Casos", format="%d"),
                "pct_seleccion": st.column_config.NumberColumn(
                    "% selección",
                    format="%.1f%%",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

    with col_graf:
        fig_json = cached_figure(
            "resumen_perfil",
            data["cache_key"],
            _df_payload(resumen),
        )
        show_cached_chart(
            fig_json,
            "chart_inicio_resumen",
            ayuda=chart_ayuda("resumen_perfil"),
        )
