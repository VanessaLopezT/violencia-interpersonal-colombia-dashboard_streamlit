# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.narrative import (
    lectura_periodo,
    render_cierre_etapa,
    render_kpis_etapa,
)
from app.page_utils import (
    _df_payload,
    cached_figure,
    lazy_tab,
    setup_page,
    show_cached_chart,
)
from app.text_es import chart_ayuda

data = setup_page("panorama")
ck = data["cache_key"]
render_kpis_etapa("panorama", data)

vista = lazy_tab(["Tendencia anual", "Lectura del periodo"], key="tab_panorama")

if vista == "Tendencia anual":
    fig_json = cached_figure("linea_anual", ck, _df_payload(data["anual"]))
    show_cached_chart(
        fig_json, "chart_panorama_linea", ayuda=chart_ayuda("linea_anual")
    )

if vista == "Lectura del periodo":
    for linea in lectura_periodo(data["anual"]):
        st.markdown(linea)
    if len(data["anual"]) >= 2:
        fig_json = cached_figure("linea_anual_pct", ck, _df_payload(data["anual"]))
        show_cached_chart(
            fig_json, "chart_panorama_pct", ayuda=chart_ayuda("linea_anual_pct")
        )

render_cierre_etapa("panorama")
