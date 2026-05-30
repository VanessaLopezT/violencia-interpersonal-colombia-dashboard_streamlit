# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.narrative import (
    render_cierre_etapa,
    render_kpis_etapa,
    sintesis_patrones,
)
from app.page_utils import (
    _df_payload,
    cached_figure,
    lazy_tab,
    setup_page,
    show_cached_chart,
)
from app.text_es import UI, chart_ayuda

data = setup_page("patrones")
ck = data["cache_key"]
render_kpis_etapa("patrones", data)

vista = lazy_tab(
    [
        "Mecanismos de lesión",
        "Escenarios del hecho",
        "Gravedad y vínculo",
        "Resumen",
    ],
    key="tab_patrones",
)

if vista == "Mecanismos de lesión":
    fig_json = cached_figure("mecanismos", ck, _df_payload(data["mecanismos"]))
    show_cached_chart(fig_json, "chart_mecanismos", ayuda=chart_ayuda("mecanismos"))

if vista == "Escenarios del hecho":
    fig_json = cached_figure("escenarios", ck, _df_payload(data["escenarios"]))
    show_cached_chart(fig_json, "chart_escenarios", ayuda=chart_ayuda("escenarios"))

if vista == "Gravedad y vínculo":
    altura_par = 400
    c1, c2 = st.columns(2)
    with c1:
        if len(data["severidad"]):
            fig_s = cached_figure(
                "severidad", ck, _df_payload(data["severidad"]), chart_height=altura_par
            )
            show_cached_chart(
                fig_s,
                "chart_severidad",
                ayuda=chart_ayuda("severidad"),
                ayuda_alineada=True,
            )
        else:
            st.info("Sin datos de severidad para la selección actual.")
    with c2:
        if len(data["agresores"]):
            fig_a = cached_figure(
                "agresores", ck, _df_payload(data["agresores"]), chart_height=altura_par
            )
            show_cached_chart(
                fig_a,
                "chart_agresores",
                ayuda=chart_ayuda("agresores"),
                ayuda_alineada=True,
            )
        else:
            st.info("Sin datos de presunto agresor para la selección actual.")

if vista == "Resumen":
    st.markdown(sintesis_patrones(data))
    st.markdown("---")
    st.markdown(
        f"Registros de valoración medicolegal, no la totalidad de la violencia ocurrida. "
        f"Subregistro, sesgo de denuncia y acceso desigual entre territorios.\n\n"
        f"**Fuente:** [{UI['source_title']}]({UI['source_url']})"
    )

render_cierre_etapa("patrones")
