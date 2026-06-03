# -*- coding: utf-8 -*-
"""Filtros del sidebar y aplicacion sobre tablas agregadas OLAP."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.analytics import FilterState, compute_slices
from app.charts import CICLO_ORDEN
from app.data_loader import Aggregates
from app.kpi import render_kpi_block
from app.text_es import UI

KEY_PERIODO = "filtro_periodo"
KEY_DEPARTAMENTO = "filtro_departamento"
KEY_MUNICIPIO = "filtro_municipio"
KEY_SEXO = "filtro_sexo"
KEY_ZONA = "filtro_zona"
KEY_ETNIA = "filtro_etnia"
KEY_CICLO = "filtro_ciclo"
CANON_KEY = "canonical_filters"
TOTAL_ETAPAS = 4


def _default_canonical(years: list[int]) -> dict[str, object]:
    return {
        "period": (int(years[0]), int(years[-1])),
        "dept": UI["todos"],
        "muni": UI["todos_municipio"],
        "sexo": UI["todos_sexo"],
        "zona": UI["todos_zona"],
        "etnia": UI["todos_etnia"],
        "ciclo": UI["todos_ciclo"],
    }


def _load_canonical(years: list[int]) -> dict[str, object]:
    if CANON_KEY not in st.session_state:
        st.session_state[CANON_KEY] = _default_canonical(years)
    canon = st.session_state[CANON_KEY]
    if _periodo_malformado(canon.get("period"), years):
        canon["period"] = _coerce_periodo(canon.get("period"), years)
    return canon


def _sync_widgets_from_canonical(years: list[int]) -> None:
    """Restaura widgets solo si perdieron estado (p. ej. al cambiar de sección)."""
    canon = _load_canonical(years)
    for widget_key, canon_key in (
        (KEY_PERIODO, "period"),
        (KEY_DEPARTAMENTO, "dept"),
        (KEY_MUNICIPIO, "muni"),
        (KEY_SEXO, "sexo"),
        (KEY_ZONA, "zona"),
        (KEY_ETNIA, "etnia"),
        (KEY_CICLO, "ciclo"),
    ):
        if widget_key not in st.session_state:
            st.session_state[widget_key] = canon[canon_key]


def _sync_canonical_from_widgets(
    years: list[int],
    *,
    period: tuple[int, int],
    dept: str,
    municipio: str,
    sexo: str,
    zona: str,
    etnia: str,
    ciclo: str,
) -> None:
    canon = _load_canonical(years)
    canon["period"] = period
    canon["dept"] = dept
    canon["muni"] = municipio
    canon["sexo"] = sexo
    canon["zona"] = zona
    canon["etnia"] = etnia
    canon["ciclo"] = ciclo


def _on_departamento_change(years: list[int]) -> None:
    """Limpia municipio solo cuando el usuario cambia departamento."""
    canon = _load_canonical(years)
    nuevo = st.session_state[KEY_DEPARTAMENTO]
    if str(canon["dept"]) != str(nuevo):
        canon["muni"] = UI["todos_municipio"]
        st.session_state[KEY_MUNICIPIO] = UI["todos_municipio"]
    canon["dept"] = nuevo


def _periodo_malformado(value: object, years: list[int]) -> bool:
    """True si el valor no es un rango de años utilizable por el slider."""
    lo, hi = int(years[0]), int(years[-1])
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        return True
    try:
        a, b = int(value[0]), int(value[1])
    except (TypeError, ValueError):
        return True
    return not (lo <= a <= hi and lo <= b <= hi)


def _coerce_periodo(value: object, years: list[int]) -> tuple[int, int]:
    """Asegura un rango (min, max) válido para el slider de años."""
    lo, hi = int(years[0]), int(years[-1])
    if isinstance(value, (tuple, list)) and len(value) == 2:
        a, b = int(value[0]), int(value[1])
    elif isinstance(value, int):
        a = b = int(value)
    else:
        return lo, hi
    a = max(lo, min(hi, a))
    b = max(lo, min(hi, b))
    if a > b:
        a, b = b, a
    return a, b


def _init_filter_defaults(years: list[int]) -> None:
    """Inicializa almacén canónico; no resetea al cambiar de sección."""
    _load_canonical(years)
    _sync_widgets_from_canonical(years)


def _ensure_selected_in_options(
    key: str, options: list[str], fallback: str
) -> list[str]:
    """Mantiene la selección actual aunque no esté en la lista dinámica (p. ej. top 50)."""
    current = st.session_state.get(key, fallback)
    if current != fallback and current not in options:
        return options + [current]
    return options


@st.cache_data
def apply_filters(
    _aggs: Aggregates, f: FilterState, _slice_version: int = 5
) -> dict[str, Any]:
    return compute_slices(_aggs, f)


def _reset_filters(years: list[int]) -> None:
    canon = _default_canonical(years)
    st.session_state[CANON_KEY] = canon
    st.session_state[KEY_PERIODO] = canon["period"]
    st.session_state[KEY_DEPARTAMENTO] = canon["dept"]
    st.session_state[KEY_MUNICIPIO] = canon["muni"]
    st.session_state[KEY_SEXO] = canon["sexo"]
    st.session_state[KEY_ZONA] = canon["zona"]
    st.session_state[KEY_ETNIA] = canon["etnia"]
    st.session_state[KEY_CICLO] = canon["ciclo"]
    apply_filters.clear()
    st.rerun()


def _municipios_opciones(
    aggs: Aggregates, year_min: int, year_max: int, departamento: str
) -> list[str]:
    t = aggs.territorial
    m = (t["anio_hecho"] >= year_min) & (t["anio_hecho"] <= year_max)
    if departamento != UI["todos"]:
        m &= t["departamento_hecho"] == departamento
    ranking = (
        t.loc[m]
        .groupby("municipio_hecho", as_index=False)["casos"]
        .sum()
        .sort_values("casos", ascending=False)
    )
    limite = None if departamento != UI["todos"] else 50
    if limite:
        ranking = ranking.head(limite)
    return ranking["municipio_hecho"].astype(str).tolist()


def _opciones_unicas(
    df: pd.DataFrame, col: str, orden: list[str] | None = None
) -> list[str]:
    presentes = sorted(df[col].dropna().astype(str).unique())
    if orden:
        ordered = [v for v in orden if v in presentes]
        extra = [v for v in presentes if v not in orden]
        return ordered + extra
    return presentes


def render_sidebar(
    aggs: Aggregates,
    etapa: int | None = None,
    section_id: str | None = None,
) -> tuple[FilterState, dict[str, Any]]:
    years = sorted(int(y) for y in aggs.filtros["anio_hecho"].unique())
    _init_filter_defaults(years)

    st.sidebar.markdown("### Filtros")

    if st.sidebar.button(UI["reset"], type="secondary", use_container_width=True):
        _reset_filters(years)

    yr = st.sidebar.slider(
        UI["periodo"],
        min_value=int(years[0]),
        max_value=int(years[-1]),
        step=1,
        key=KEY_PERIODO,
    )
    year_min, year_max = int(yr[0]), int(yr[1])

    st.sidebar.caption(UI["filtros_territorio"])
    depts = [UI["todos"]] + sorted(aggs.filtros["departamento_hecho"].unique())
    depts = _ensure_selected_in_options(KEY_DEPARTAMENTO, depts, UI["todos"])
    dept = st.sidebar.selectbox(
        UI["territorio"],
        depts,
        key=KEY_DEPARTAMENTO,
        on_change=_on_departamento_change,
        args=(years,),
    )

    muni_opts = [UI["todos_municipio"]] + _municipios_opciones(
        aggs, year_min, year_max, dept
    )
    if dept == UI["todos"]:
        muni_opts = _ensure_selected_in_options(
            KEY_MUNICIPIO, muni_opts, UI["todos_municipio"]
        )
    if dept == UI["todos"]:
        st.sidebar.caption(UI["municipio_hint"])
    municipio = st.sidebar.selectbox(
        UI["municipio"],
        muni_opts,
        key=KEY_MUNICIPIO,
    )

    zonas = [UI["todos_zona"]] + _opciones_unicas(aggs.filtros, "zona_hecho")
    zonas = _ensure_selected_in_options(KEY_ZONA, zonas, UI["todos_zona"])
    zona = st.sidebar.selectbox(UI["zona"], zonas, key=KEY_ZONA)

    st.sidebar.caption(UI["filtros_victima"])
    sexo_opts = [UI["todos_sexo"], "Hombre", "Mujer"]
    sexo = st.sidebar.selectbox(
        UI["sexo_victima"],
        sexo_opts,
        key=KEY_SEXO,
    )

    etnias = [UI["todos_etnia"]] + _opciones_unicas(aggs.filtros, "pertenencia_etnica")
    etnias = _ensure_selected_in_options(KEY_ETNIA, etnias, UI["todos_etnia"])
    etnia = st.sidebar.selectbox(UI["pertenencia_etnica"], etnias, key=KEY_ETNIA)

    ciclos_presentes = _opciones_unicas(aggs.filtros, "ciclo_vital", CICLO_ORDEN)
    ciclo_opts = [UI["todos_ciclo"]] + ciclos_presentes
    ciclo_opts = _ensure_selected_in_options(KEY_CICLO, ciclo_opts, UI["todos_ciclo"])
    ciclo = st.sidebar.selectbox(
        UI["ciclo_vital"],
        ciclo_opts,
        key=KEY_CICLO,
    )

    _sync_canonical_from_widgets(
        years,
        period=(year_min, year_max),
        dept=dept,
        municipio=municipio,
        sexo=sexo,
        zona=zona,
        etnia=etnia,
        ciclo=ciclo,
    )

    f = FilterState(
        year_min=year_min,
        year_max=year_max,
        departamento=dept,
        municipio=municipio,
        sexo=sexo,
        zona=zona,
        pertenencia_etnica=etnia,
        ciclo_vital=ciclo,
    )
    data = apply_filters(aggs, f)
    st.sidebar.divider()
    render_kpi_block(UI["casos_filtro"], f"{data['casos']:,}", container=st.sidebar)
    render_kpi_block(
        UI["pct_total"], f"{data['pct_total']:.1f}%", spaced=True, container=st.sidebar
    )

    if etapa is not None:
        st.sidebar.divider()
        st.sidebar.caption(f"Sección {etapa} de {TOTAL_ETAPAS}")
        st.sidebar.progress(etapa / TOTAL_ETAPAS)

    if section_id is not None:
        from app.nav import render_sidebar_section_nav

        if etapa is None:
            st.sidebar.divider()
        render_sidebar_section_nav(section_id)

    return f, data
