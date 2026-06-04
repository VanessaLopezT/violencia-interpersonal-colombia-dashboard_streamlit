# -*- coding: utf-8 -*-
"""Componentes narrativos reutilizables para el recorrido analitico."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.kpi import render_kpi_row
from app.nav import nav_button
from app.text_es import STORY, UI


def render_apertura(etapa_key: str, data: dict[str, Any]) -> None:
    story = STORY[etapa_key]
    st.markdown(f"### {story['pregunta']}")
    st.caption(_HALLAZGO_BUILDERS[etapa_key](data))


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def _fmt_int(value: int | float) -> str:
    return f"{int(value):,}"


def _hallazgo_panorama(data: dict[str, Any]) -> str:
    anual = data["anual"]
    if anual.empty:
        return "No hay casos en el periodo y filtros seleccionados."
    imax = anual.loc[anual["casos"].idxmax()]
    imin = anual.loc[anual["casos"].idxmin()]
    return (
        f"En su selección ({_fmt_int(data['casos'])} casos), el año con más registros es "
        f"{int(imax['anio_hecho'])} ({_fmt_int(imax['casos'])} casos) y el de menos, "
        f"{int(imin['anio_hecho'])} ({_fmt_int(imin['casos'])} casos)."
    )


def _hallazgo_territorio(data: dict[str, Any]) -> str:
    dept = data["dept"]
    if dept.empty:
        return "No hay casos territoriales con los filtros actuales."
    lider = dept.iloc[0]
    top3_pct = dept.head(3)["pct"].sum() if len(dept) >= 3 else dept["pct"].sum()
    n = min(3, len(dept))
    nombres = ", ".join(dept.head(n)["departamento_hecho"].astype(str).tolist())
    return (
        f"Lidera {lider['departamento_hecho']} ({_fmt_pct(lider['pct'])} de la selección). "
        f"Los {n} departamentos con más casos ({nombres}) suman {_fmt_pct(top3_pct)}."
    )


def _hallazgo_personas(data: dict[str, Any]) -> str:
    sexo = data["sexo"]
    if sexo.empty:
        return "No hay datos de perfil de víctima en la selección actual."
    total = int(sexo["casos"].sum())
    masc = int(sexo.loc[sexo["sexo_victima"] == "Hombre", "casos"].sum())
    fem = int(sexo.loc[sexo["sexo_victima"] == "Mujer", "casos"].sum())
    pct_m = masc / total * 100 if total else 0
    pct_f = fem / total * 100 if total else 0
    edad = data["edad_sexo"]
    grupo = "N/D"
    if len(edad):
        grupo = str(edad.groupby("grupo_edad_quinquenal")["casos"].sum().idxmax())
    dia = data.get("dia_top", "N/D")
    franja = data.get("franja_top", "N/D")
    return (
        f"En la selección: {_fmt_pct(pct_m)} hombres y {_fmt_pct(pct_f)} mujeres; "
        f"grupo etario con más casos, {grupo}; combinación más frecuente, {dia} en {franja}."
    )


def _hallazgo_patrones(data: dict[str, Any]) -> str:
    mec = data["mecanismos"]
    esc = data["escenarios"]
    if mec.empty and esc.empty:
        return "No hay patrones de lesión registrados con los filtros actuales."
    partes: list[str] = []
    if len(mec):
        top = mec.iloc[0]
        partes.append(
            f"mecanismo más frecuente, {top['categoria']} ({_fmt_pct(top['pct'])} de la selección)"
        )
    if len(esc):
        top = esc.iloc[0]
        partes.append(
            f"escenario principal, {top['categoria']} ({_fmt_pct(top['pct'])} de la selección)"
        )
    return "Según los filtros activos: " + "; ".join(partes) + "."


_HALLAZGO_BUILDERS = {
    "panorama": _hallazgo_panorama,
    "territorio": _hallazgo_territorio,
    "personas": _hallazgo_personas,
    "patrones": _hallazgo_patrones,
}


def _kpi_panorama(data: dict[str, Any]) -> list[tuple[str, str]]:
    anual = data["anual"]
    if anual.empty:
        return [
            ("Casos en la selección", "0"),
            ("Año de mayor registro", "N/D"),
            ("Año de menor registro", "N/D"),
            ("Variación entre extremos", "N/D"),
        ]
    imax = anual.loc[anual["casos"].idxmax()]
    imin = anual.loc[anual["casos"].idxmin()]
    var = (
        ((imax["casos"] - imin["casos"]) / imin["casos"] * 100) if imin["casos"] else 0
    )
    return [
        ("Casos en la selección", _fmt_int(data["casos"])),
        (
            "Año de mayor registro",
            f"{int(imax['anio_hecho'])} ({_fmt_int(imax['casos'])})",
        ),
        (
            "Año de menor registro",
            f"{int(imin['anio_hecho'])} ({_fmt_int(imin['casos'])})",
        ),
        ("Variación entre extremos", _fmt_pct(var)),
    ]


def _kpi_territorio(data: dict[str, Any]) -> list[tuple[str, str]]:
    dept = data["dept"]
    zona = data["zona"]
    muni = data.get("muni_top")
    top3 = (
        dept.head(3)["pct"].sum()
        if len(dept) >= 3
        else (dept["pct"].sum() if len(dept) else 0)
    )
    urbana = zona.loc[
        zona["zona_hecho"].astype(str).str.contains("Cabecera", case=False, na=False),
        "pct",
    ].sum()
    muni_label = "N/D"
    if muni is not None and len(muni):
        muni_label = (
            f"{muni.iloc[0]['municipio_hecho']}\n"
            f"{_fmt_int(muni.iloc[0]['casos'])} casos"
        )
    return [
        ("Departamento líder", str(data["dept_lider"])),
        ("Participación del top 3", _fmt_pct(top3)),
        ("Zona urbana (cabecera)", _fmt_pct(urbana)),
        ("Municipio con más casos", muni_label),
    ]


def _kpi_personas(data: dict[str, Any]) -> list[tuple[str, str]]:
    sexo = data["sexo"]
    total = sexo["casos"].sum() if len(sexo) else 0
    masc = sexo.loc[sexo["sexo_victima"] == "Hombre", "casos"].sum() if len(sexo) else 0
    fem = sexo.loc[sexo["sexo_victima"] == "Mujer", "casos"].sum() if len(sexo) else 0
    pct_m = (masc / total * 100) if total else 0
    pct_f = (fem / total * 100) if total else 0
    edad = data["edad_sexo"]
    grupo_modal = "N/D"
    if len(edad):
        grupo_modal = str(edad.groupby("grupo_edad_quinquenal")["casos"].sum().idxmax())
    dia = data.get("dia_top", "N/D")
    franja = data.get("franja_top", "N/D")
    return [
        ("Hombres", _fmt_pct(pct_m)),
        ("Mujeres", _fmt_pct(pct_f)),
        ("Grupo etario modal", grupo_modal),
        ("Día y franja", f"{dia}\n{franja}"),
    ]


def _kpi_patrones(data: dict[str, Any]) -> list[tuple[str, str]]:
    mec = data["mecanismos"]
    esc = data["escenarios"]
    sev = data.get("severidad", pd.DataFrame())
    agr = data.get("agresores", pd.DataFrame())
    mec_top = mec.iloc[0] if len(mec) else None
    esc_top = esc.iloc[0] if len(esc) else None
    sev_top = sev.iloc[0] if len(sev) else None
    agr_top = agr.iloc[0] if len(agr) else None
    return [
        (
            "Mecanismo principal",
            str(mec_top["categoria"]) if mec_top is not None else "N/D",
        ),
        (
            "Escenario principal",
            str(esc_top["categoria"]) if esc_top is not None else "N/D",
        ),
        (
            "Gravedad modal",
            (
                f"{sev_top['categoria']}\n{_fmt_pct(sev_top['pct'])}"
                if sev_top is not None
                else "N/D"
            ),
        ),
        (
            "Vínculo con agresor modal",
            str(agr_top["categoria"]) if agr_top is not None else "N/D",
        ),
    ]


_KPI_BUILDERS = {
    "panorama": _kpi_panorama,
    "territorio": _kpi_territorio,
    "personas": _kpi_personas,
    "patrones": _kpi_patrones,
}


def render_kpis_etapa(etapa_key: str, data: dict[str, Any]) -> None:
    render_kpi_row(_KPI_BUILDERS[etapa_key](data))


def render_cierre_etapa(etapa_key: str) -> None:
    story = STORY[etapa_key]
    st.divider()
    if story["siguiente_path"]:
        nav_button(
            f"Siguiente: {story['siguiente_titulo']}",
            story["siguiente_path"],
            key=f"nav_next_{etapa_key}",
        )
    else:
        nav_button(
            UI["volver_inicio"],
            "streamlit_app.py",
            key="nav_home",
        )


def lectura_periodo(anual: pd.DataFrame) -> list[str]:
    if anual.empty or len(anual) < 2:
        return ["Seleccione al menos dos años para comparar."]
    imax = anual.loc[anual["casos"].idxmax()]
    imin = anual.loc[anual["casos"].idxmin()]
    lines = [
        f"El año **{int(imax['anio_hecho'])}** concentra el mayor número de registros "
        f"({_fmt_int(imax['casos'])} casos).",
        f"El mínimo en la selección corresponde a **{int(imin['anio_hecho'])}** "
        f"({_fmt_int(imin['casos'])} casos).",
    ]
    y2020 = anual.loc[anual["anio_hecho"] == 2020, "casos"]
    if len(y2020):
        lines.append(
            "En **2020** se observa una caída marcada que puede relacionarse con restricciones "
            "de movilidad o cambios en el registro, no necesariamente con menor violencia real."
        )
    ultimo = anual.iloc[-1]
    lines.append(
        f"Hacia el cierre del periodo ({int(ultimo['anio_hecho'])}), la serie muestra "
        f"{_fmt_int(ultimo['casos'])} casos registrados."
    )
    return lines


def sintesis_patrones(data: dict[str, Any]) -> str:
    mec = data["mecanismos"]
    esc = data["escenarios"]
    sev = data.get("severidad", pd.DataFrame())
    agr = data.get("agresores", pd.DataFrame())
    parts = []
    if len(mec):
        top = mec.iloc[0]
        parts.append(
            f"El mecanismo **{top['categoria']}** concentra {_fmt_pct(top['pct'])} de los casos."
        )
    if len(esc):
        top = esc.iloc[0]
        parts.append(
            f"El escenario **{top['categoria']}** aparece en {_fmt_pct(top['pct'])} de los registros."
        )
    if len(sev):
        top = sev.iloc[0]
        parts.append(
            f"La categoría de gravedad **{top['categoria']}** es la más frecuente "
            f"({_fmt_pct(top['pct'])})."
        )
    if len(agr):
        top = agr.iloc[0]
        parts.append(
            f"El presunto agresor **{top['categoria']}** aparece en {_fmt_pct(top['pct'])} de los casos."
        )
    parts.append(
        "Son registros administrativos; no miden la violencia no denunciada "
        "ni permiten inferir causas."
    )
    return " ".join(parts)
