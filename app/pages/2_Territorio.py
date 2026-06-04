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
    cached_figure,
    cached_muni_figure,
    lazy_tab,
    setup_page,
    show_cached_chart,
)
from app.text_es import DEPTO_BOGOTA, chart_ayuda
from app.charts import norm_depto_geo_key, POBLACION_DEPARTAMENTOS


def _drill_cache_key(cache_key: tuple, dept_sel: str) -> tuple:
    return (*cache_key, "drill_territorial", dept_sel)


@st.fragment
def _drill_municipios(data: dict, cache_key: tuple) -> None:
    top_depts = data["dept_drill"].head(10)["departamento_hecho"].tolist()
    if not top_depts:
        st.info("No hay datos territoriales para la selección actual.")
        return
    dept_sel = st.selectbox("Departamento", top_depts, key="drill_departamento")
    drill_ck = _drill_cache_key(cache_key, dept_sel)

    if dept_sel == DEPTO_BOGOTA:
        loc = data.get("loc_por_depto_drill")
        if loc is None or loc.empty:
            st.info(
                "Bogotá D.C. es una sola ciudad. Ejecute `python analysis/run.py` "
                "para regenerar agregados con localidades."
            )
            return
        loc_depto = loc.loc[loc["departamento_hecho"] == dept_sel].sort_values(
            "casos", ascending=False
        )
        if loc_depto.empty:
            st.info(
                "No hay localidades registradas para Bogotá D.C. en la selección actual."
            )
            return
        fig_json = cached_muni_figure(
            drill_ck,
            _df_payload(loc_depto),
            dept_sel,
            label_col="localidad_hecho",
            title="Top 5 localidades en Bogotá D.C.",
        )
        show_cached_chart(
            fig_json,
            f"chart_loc_{dept_sel}",
            ayuda=chart_ayuda("localidades"),
        )
        return

    muni_depto = (
        data["muni_por_depto_drill"]
        .loc[data["muni_por_depto_drill"]["departamento_hecho"] == dept_sel]
        .sort_values("casos", ascending=False)
    )
    if muni_depto["municipio_hecho"].nunique() <= 1:
        st.info(f"{dept_sel} no tiene desglose municipal en los datos.")
        return
    fig_json = cached_muni_figure(drill_ck, _df_payload(muni_depto), dept_sel)
    show_cached_chart(
        fig_json, f"chart_muni_{dept_sel}", ayuda=chart_ayuda("municipios")
    )


data = setup_page("territorio")
ck = data["cache_key"]
render_kpis_etapa("territorio", data)

metric_choice = st.radio(
    "Métrica de análisis",
    ["Casos absolutos", "Tasa por 100.000 habitantes"],
    horizontal=True,
    help="La tasa por 100.000 habitantes normaliza los casos según la población estimada de cada departamento (DANE 2020), lo que permite una comparación justa entre regiones de diferente tamaño.",
    key="territorio_metric_choice"
)

vista = lazy_tab(
    [
        "Ranking departamental",
        "Mapa de calor temporal",
        "Urbano y rural",
        "Detalle territorial",
    ],
    key="tab_territorio",
)

if vista == "Ranking departamental":
    if metric_choice == "Tasa por 100.000 habitantes":
        df_dept = data["dept"].copy()
        df_dept = df_dept[df_dept["departamento_hecho"] != "Sin informacion"]
        df_dept["norm_key"] = df_dept["departamento_hecho"].map(norm_depto_geo_key)
        df_dept["poblacion"] = df_dept["norm_key"].map(POBLACION_DEPARTAMENTOS)
        df_dept["tasa"] = (df_dept["casos"] / df_dept["poblacion"]) * 100000
        df_dept = df_dept.dropna(subset=["poblacion"]).sort_values("tasa", ascending=False)
        fig_json = cached_figure("dept_tasa_top10", ck, _df_payload(df_dept.head(10)))
        chart_id_ayuda = "dept_tasa_top10"
    else:
        fig_json = cached_figure("dept_top10", ck, _df_payload(data["dept"].head(10)))
        chart_id_ayuda = "dept_top10"

    show_cached_chart(
        fig_json, "chart_territorio_dept", ayuda=chart_ayuda(chart_id_ayuda)
    )

if vista == "Mapa de calor temporal":
    st.subheader("Distribución geográfica de casos en el tiempo")
    st.caption(chart_ayuda("mapa_temporal"))

    from app.page_utils import load_colombia_geojson
    from app.charts import mapa_colombia_timeline

    geojson = load_colombia_geojson()
    f = data["filter_state"]
    metric = "tasa" if metric_choice == "Tasa por 100.000 habitantes" else "casos"

    fig = mapa_colombia_timeline(data["mapa_drill"], geojson, f.year_min, f.year_max, metric=metric)
    st.plotly_chart(
        fig,
        use_container_width=True,
        key="chart_territorio_mapa",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
        },
    )

if vista == "Urbano y rural":
    fig_json = cached_figure("zona", ck, _df_payload(data["zona"]))
    show_cached_chart(fig_json, "chart_territorio_zona", ayuda=chart_ayuda("zona"))

if vista == "Detalle territorial":
    _drill_municipios(data, ck)

render_cierre_etapa("territorio")
