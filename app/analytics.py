# -*- coding: utf-8 -*-
"""Agregacion OLAP sobre tablas precomputadas (sin dependencia de Streamlit)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.data_loader import Aggregates
from app.text_es import UI, normalizar_franja


@dataclass(frozen=True)
class FilterState:
    year_min: int
    year_max: int
    departamento: str
    municipio: str
    sexo: str
    zona: str
    pertenencia_etnica: str
    ciclo_vital: str


def _mask(
    df: pd.DataFrame,
    f: FilterState,
    *,
    ignore_municipio: bool = False,
    ignore_departamento: bool = False,
) -> pd.Series:
    m = (df["anio_hecho"] >= f.year_min) & (df["anio_hecho"] <= f.year_max)
    if not ignore_departamento and f.departamento != UI["todos"]:
        m &= df["departamento_hecho"] == f.departamento
    if not ignore_municipio and f.municipio != UI["todos_municipio"]:
        m &= df["municipio_hecho"] == f.municipio
    if f.sexo != UI["todos_sexo"]:
        m &= df["sexo_victima"] == f.sexo
    if f.zona != UI["todos_zona"]:
        m &= df["zona_hecho"] == f.zona
    if f.pertenencia_etnica != UI["todos_etnia"]:
        m &= df["pertenencia_etnica"] == f.pertenencia_etnica
    if f.ciclo_vital != UI["todos_ciclo"]:
        m &= df["ciclo_vital"] == f.ciclo_vital
    return m


def _top_dia_franja(dh: pd.DataFrame) -> tuple[str, str]:
    if dh.empty:
        return "N/D", "N/D"
    row = dh.loc[dh["casos"].idxmax()]
    return str(row["dia_hecho"]), str(row["rango_hora"])


def _patron_slice(pat: pd.DataFrame, tipo: str, casos: int) -> pd.DataFrame:
    out = pat[pat["tipo"] == tipo].groupby("categoria", as_index=False)["casos"].sum()
    out["pct"] = out["casos"] / casos * 100 if casos else 0
    return out.sort_values("casos", ascending=False)


def compute_slices(aggs: Aggregates, f: FilterState) -> dict[str, Any]:
    filt = aggs.filtros.loc[_mask(aggs.filtros, f)]
    casos = int(filt["casos"].sum())
    pct = (casos / aggs.total_nacional * 100) if aggs.total_nacional else 0.0
    cache_key = (
        f.year_min,
        f.year_max,
        f.departamento,
        f.municipio,
        f.sexo,
        f.zona,
        f.pertenencia_etnica,
        f.ciclo_vital,
        casos,
    )

    anual = (
        filt.groupby("anio_hecho", as_index=False)["casos"]
        .sum()
        .sort_values("anio_hecho")
    )
    anual = anual.copy()
    anual["pct_total"] = (
        anual["casos"] / aggs.total_nacional * 100 if aggs.total_nacional else 0
    )

    territorial = aggs.territorial.loc[_mask(aggs.territorial, f)]
    dept = (
        territorial.groupby("departamento_hecho", as_index=False)["casos"]
        .sum()
        .sort_values("casos", ascending=False)
    )
    dept["pct"] = dept["casos"] / casos * 100 if casos else 0

    muni = (
        territorial.groupby(["departamento_hecho", "municipio_hecho"], as_index=False)[
            "casos"
        ]
        .sum()
        .sort_values("casos", ascending=False)
    )

    loc_por_depto = pd.DataFrame()
    if "localidad_hecho" in territorial.columns:
        loc = (
            territorial.loc[territorial["localidad_hecho"] != "Sin informacion"]
            .groupby(["departamento_hecho", "localidad_hecho"], as_index=False)["casos"]
            .sum()
            .sort_values("casos", ascending=False)
        )
        loc_por_depto = loc

    territorial_drill = aggs.territorial.loc[
        _mask(aggs.territorial, f, ignore_municipio=True, ignore_departamento=True)
    ]
    dept_drill = (
        territorial_drill.groupby("departamento_hecho", as_index=False)["casos"]
        .sum()
        .sort_values("casos", ascending=False)
    )
    muni_drill = (
        territorial_drill.groupby(
            ["departamento_hecho", "municipio_hecho"], as_index=False
        )["casos"]
        .sum()
        .sort_values("casos", ascending=False)
    )
    loc_drill = pd.DataFrame()
    if "localidad_hecho" in territorial_drill.columns:
        loc_drill = (
            territorial_drill.loc[
                territorial_drill["localidad_hecho"] != "Sin informacion"
            ]
            .groupby(["departamento_hecho", "localidad_hecho"], as_index=False)["casos"]
            .sum()
            .sort_values("casos", ascending=False)
        )
    mapa_drill = territorial_drill.groupby(
        ["departamento_hecho", "anio_hecho"], as_index=False
    )["casos"].sum()

    zona = filt.groupby("zona_hecho", as_index=False)["casos"].sum()
    zona["pct"] = zona["casos"] / casos * 100 if casos else 0

    etnia = (
        filt.groupby("pertenencia_etnica", as_index=False)["casos"]
        .sum()
        .sort_values("casos", ascending=False)
    )
    etnia["pct"] = etnia["casos"] / casos * 100 if casos else 0

    demo = aggs.demografia.loc[_mask(aggs.demografia, f)]
    edad_sexo = demo.groupby(["sexo_victima", "grupo_edad_quinquenal"], as_index=False)[
        "casos"
    ].sum()
    sexo = demo.groupby("sexo_victima", as_index=False)["casos"].sum()
    sexo["pct"] = sexo["casos"] / casos * 100 if casos else 0
    ciclo = demo.groupby(["sexo_victima", "ciclo_vital"], as_index=False)["casos"].sum()

    pat = aggs.patrones.loc[_mask(aggs.patrones, f)]
    esc = _patron_slice(pat, "escenario", casos)
    mec = _patron_slice(pat, "mecanismo", casos)
    sev = _patron_slice(pat, "severidad", casos)
    agr = _patron_slice(pat, "agresor", casos)

    dh = aggs.dia_hora.loc[_mask(aggs.dia_hora, f)].copy()
    dh["rango_hora"] = dh["rango_hora"].map(normalizar_franja)
    dh = dh.groupby(["dia_hecho", "rango_hora"], as_index=False)["casos"].sum()
    dia_top, franja_top = _top_dia_franja(dh)

    dept_lider = dept.iloc[0]["departamento_hecho"] if len(dept) else "N/D"

    return {
        "cache_key": cache_key,
        "casos": casos,
        "pct_total": pct,
        "dept_lider": dept_lider,
        "anual": anual,
        "dept": dept,
        "dept_drill": dept_drill,
        "zona": zona,
        "etnia": etnia,
        "muni_top": muni.head(1),
        "muni_por_depto": muni,
        "loc_por_depto": loc_por_depto,
        "muni_por_depto_drill": muni_drill,
        "loc_por_depto_drill": loc_drill,
        "mapa_drill": mapa_drill,
        "edad_sexo": edad_sexo,
        "sexo": sexo,
        "ciclo": ciclo,
        "escenarios": esc.head(8),
        "mecanismos": mec.head(8),
        "severidad": sev,
        "agresores": agr.head(8),
        "dia_hora": dh,
        "dia_top": dia_top,
        "franja_top": franja_top,
        "filter_state": f,
    }


def _top_categoria(
    df: pd.DataFrame, col: str, casos: int
) -> tuple[str, int, float] | None:
    if df.empty or casos <= 0 or col not in df.columns:
        return None
    row = df.sort_values("casos", ascending=False).iloc[0]
    pct = (
        float(row["pct"]) if "pct" in df.columns else float(row["casos"]) / casos * 100
    )
    return str(row[col]), int(row["casos"]), pct


def resumen_perfil_seleccion(data: dict[str, Any]) -> pd.DataFrame:
    """Tabla integrada del perfil bajo todos los filtros activos."""
    f: FilterState = data["filter_state"]
    casos = int(data["casos"])
    rows: list[dict[str, object]] = []

    def append(dimension: str, detalle: str, n: int, pct: float) -> None:
        rows.append(
            {
                "dimension": dimension,
                "detalle": detalle,
                "casos": n,
                "pct_seleccion": round(pct, 1),
            }
        )

    append("Años", f"{f.year_min}–{f.year_max}", casos, 100.0 if casos else 0.0)

    if f.municipio != UI["todos_municipio"]:
        territorio = f"{f.departamento} · {f.municipio}"
    elif f.departamento != UI["todos"]:
        territorio = f.departamento
    else:
        territorio = f"Todo el país (lidera {data.get('dept_lider', 'N/D')})"
    append("Territorio", territorio, casos, 100.0 if casos else 0.0)

    if f.sexo != UI["todos_sexo"]:
        append("Sexo", f"Filtro activo: {f.sexo}", casos, 100.0)
    elif top := _top_categoria(data.get("sexo", pd.DataFrame()), "sexo_victima", casos):
        append("Sexo predominante", top[0], top[1], top[2])

    if f.zona != UI["todos_zona"]:
        append("Zona del hecho", f"Filtro activo: {f.zona}", casos, 100.0)
    elif top := _top_categoria(data.get("zona", pd.DataFrame()), "zona_hecho", casos):
        append("Zona del hecho", top[0], top[1], top[2])

    if f.pertenencia_etnica != UI["todos_etnia"]:
        append(
            "Pertenencia étnica", f"Filtro activo: {f.pertenencia_etnica}", casos, 100.0
        )
    elif top := _top_categoria(
        data.get("etnia", pd.DataFrame()), "pertenencia_etnica", casos
    ):
        append("Pertenencia étnica", top[0], top[1], top[2])

    if f.ciclo_vital != UI["todos_ciclo"]:
        append("Ciclo vital", f"Filtro activo: {f.ciclo_vital}", casos, 100.0)
    else:
        ciclo_agg = (
            data.get("ciclo", pd.DataFrame())
            .groupby("ciclo_vital", as_index=False)["casos"]
            .sum()
        )
        ciclo_agg["pct"] = ciclo_agg["casos"] / casos * 100 if casos else 0
        if top := _top_categoria(ciclo_agg, "ciclo_vital", casos):
            append("Ciclo vital", top[0], top[1], top[2])

    for dimension, key in (
        ("Mecanismo de lesión", "mecanismos"),
        ("Escenario", "escenarios"),
        ("Gravedad medicolegal", "severidad"),
        ("Presunto agresor", "agresores"),
    ):
        if top := _top_categoria(data.get(key, pd.DataFrame()), "categoria", casos):
            append(dimension, top[0], top[1], top[2])

    dh = data.get("dia_hora", pd.DataFrame())
    if not dh.empty and casos > 0:
        pico = dh.loc[dh["casos"].idxmax()]
        append(
            "Momento más frecuente",
            f"{pico['dia_hecho']} · {pico['rango_hora']}",
            int(pico["casos"]),
            float(pico["casos"]) / casos * 100,
        )

    return pd.DataFrame(rows)
