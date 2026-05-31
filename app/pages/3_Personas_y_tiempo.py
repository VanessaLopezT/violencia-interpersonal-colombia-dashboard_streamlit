# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.narrative import render_cierre_etapa, render_kpis_etapa
from app.page_utils import (
    _df_payload,
    cached_ciclo_figure,
    cached_figure,
    lazy_tab,
    setup_page,
    show_cached_chart,
)
from app.text_es import SEXO_OPCIONES, chart_ayuda


@st.fragment
def _perfil_ciclo(data: dict, cache_key: tuple) -> None:
    fig_json = cached_figure("edad_sexo", cache_key, _df_payload(data["edad_sexo"]))
    show_cached_chart(fig_json, "chart_edad_sexo", ayuda=chart_ayuda("edad_sexo"))

    sexo_resaltar = st.radio(
        "Ver ciclo vital por sexo",
        SEXO_OPCIONES,
        horizontal=True,
        key="resaltar_sexo",
    )
    ayuda_ciclo = (
        chart_ayuda("ciclo_ambos")
        if sexo_resaltar == "Ambos"
        else chart_ayuda("ciclo_sexo", sexo=sexo_resaltar.lower())
    )
    ciclo_json = cached_ciclo_figure(
        cache_key, _df_payload(data["ciclo"]), sexo_resaltar
    )
    show_cached_chart(ciclo_json, f"chart_ciclo_{sexo_resaltar}", ayuda=ayuda_ciclo)


data = setup_page("personas")
ck = data["cache_key"]
render_kpis_etapa("personas", data)

vista = lazy_tab(["Perfil de víctimas", "Momento del hecho"], key="tab_personas")

if vista == "Perfil de víctimas":
    _perfil_ciclo(data, ck)

if vista == "Momento del hecho":
    fig_h = cached_figure("heatmap_dh", ck, _df_payload(data["dia_hora"]))
    show_cached_chart(fig_h, "chart_heatmap_dh", ayuda=chart_ayuda("heatmap_dh"))
    fig_f = cached_figure("top_franjas", ck, _df_payload(data["dia_hora"]))
    show_cached_chart(fig_f, "chart_top_franjas", ayuda=chart_ayuda("top_franjas"))

render_cierre_etapa("personas")
