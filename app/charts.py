# -*- coding: utf-8 -*-
"""Funciones Plotly para el dashboard interactivo."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.theme import (
    COLOR_PRIMARY,
    COLOR_ZONA,
    FONT_FAMILY,
    HEATMAP_SCALE,
    MAP_CHOROPLETH_SCALE,
    PALETA_GRUPO_EDAD,
    PALETTE_CATEGORICAL,
    PLOTLY_TEMPLATE,
)
from app.text_es import DEPTO_BOGOTA, normalizar_franja

DIAS_ORDEN = [
    "1 Lunes",
    "2 Martes",
    "3 Miercoles",
    "4 Jueves",
    "5 Viernes",
    "6 Sabado",
    "7 Domingo",
    "Lunes",
    "Martes",
    "Miercoles",
    "Jueves",
    "Viernes",
    "Sabado",
    "Sábado",
    "Domingo",
]

CICLO_ORDEN = [
    "(00 a 05) Primera Infancia",
    "(06 a 11) Infancia",
    "(12 a 17) Adolescencia",
    "(18 a 28) Juventud",
    "(29 a 59) Adultez",
    "(Más de 60) Adulto Mayor",
    "Sin informacion",
]

FRANJAS_ORDEN = [
    "(00:00 a 02:59)",
    "(03:00 a 05:59)",
    "(06:00 a 08:59)",
    "(09:00 a 11:59)",
    "(12:00 a 14:59)",
    "(15:00 a 17:59)",
    "(18:00 a 20:59)",
    "(21:00 a 23:59)",
    "Sin informacion",
]

EDAD_QUINQUENAL_ORDEN = [
    "(00 a 04)",
    "(05 a 09)",
    "(10 a 14)",
    "(15 a 17)",
    "(18 a 19)",
    "(20 a 24)",
    "(25 a 29)",
    "(30 a 34)",
    "(35 a 39)",
    "(40 a 44)",
    "(45 a 49)",
    "(50 a 54)",
    "(55 a 59)",
    "(60 a 64)",
    "(65 a 69)",
    "(70 a 74)",
    "(75 a 79)",
    "(80 y más)",
    "Sin informacion",
]

SEXO_ORDEN = ["Hombre", "Mujer"]

COLOR_FEMENINO = "#7B68A6"
COLOR_MASCULINO = "#3D7EA6"


def _prepare_anio(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["anio_hecho"] = pd.to_numeric(out["anio_hecho"], errors="coerce").astype(
        "Int64"
    )
    return out.dropna(subset=["anio_hecho"])


def _eje_anio(fig: go.Figure, anios: pd.Series) -> None:
    vals = sorted(int(a) for a in anios.dropna().unique())
    if not vals:
        return
    fig.update_xaxes(
        type="linear",
        tickmode="array",
        tickvals=vals,
        ticktext=[str(v) for v in vals],
        range=[vals[0] - 0.4, vals[-1] + 0.4],
    )


def _hover_casos() -> dict:
    return dict(hovertemplate=("<b>%{x}</b><br>Casos: %{y:,}<br>" "<extra></extra>"))


def _hover_bar_h() -> dict:
    return dict(hovertemplate=("<b>%{y}</b><br>Casos: %{x:,}<br>" "<extra></extra>"))


def _layout(fig: go.Figure, height: int = 420, margin: dict | None = None) -> go.Figure:
    base_margin = dict(l=56, r=56, t=60, b=56, pad=4)
    if margin:
        base_margin.update(margin)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=base_margin,
        autosize=True,
        font=dict(family=FONT_FAMILY, size=12, color="#1E293B"),
        colorway=PALETTE_CATEGORICAL,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFBFC",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(automargin=True, title_standoff=10)
    fig.update_yaxes(automargin=True, title_standoff=10)
    return fig


def _fit_outside_text(
    fig: go.Figure,
    max_value: float,
    *,
    axis: str = "x",
    padding: float = 0.15,
) -> None:
    """Evita que etiquetas textposition=outside se corten en el borde del cuadro."""
    fig.update_traces(cliponaxis=False)
    if max_value <= 0:
        max_value = 1.0
    upper = max_value * (1.0 + padding)
    if axis == "x":
        fig.update_xaxes(range=[0, upper])
    else:
        fig.update_yaxes(range=[0, upper])


def linea_anual(
    df: pd.DataFrame,
    title: str = "Tendencia anual de casos registrados",
) -> go.Figure:
    df = _prepare_anio(df)
    hover = (
        "<b>Año %{x}</b><br>Casos: %{y:,}<br>"
        "Participación del total: %{customdata[0]:.1f}%<br>"
        "<extra></extra>"
    )
    if "pct_total" in df.columns:
        custom = df[["pct_total"]]
    else:
        custom = pd.DataFrame({"pct_total": [0.0] * len(df)})
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["anio_hecho"].astype(int),
            y=df["casos"],
            mode="lines+markers",
            line=dict(width=3, color=COLOR_PRIMARY),
            marker=dict(size=8, color=COLOR_PRIMARY),
            customdata=custom,
            hovertemplate=hover,
        )
    )
    _eje_anio(fig, df["anio_hecho"])
    fig.update_layout(
        title=title,
        xaxis_title="Año",
        yaxis_title="Casos registrados",
        hovermode="x unified",
    )
    if len(df) >= 2:
        imax = df["casos"].idxmax()
        imin = df["casos"].idxmin()
        fig.add_annotation(
            x=int(df.loc[imax, "anio_hecho"]),
            y=df.loc[imax, "casos"],
            text="Máximo",
            showarrow=True,
            arrowhead=2,
            font=dict(color=COLOR_PRIMARY),
        )
        fig.add_annotation(
            x=int(df.loc[imin, "anio_hecho"]),
            y=df.loc[imin, "casos"],
            text="Mínimo",
            showarrow=True,
            arrowhead=2,
            font=dict(color=COLOR_PRIMARY),
        )
    ymax = float(df["casos"].max()) if len(df) else 1.0
    _fit_outside_text(fig, ymax, axis="y", padding=0.12)
    return _layout(fig, margin=dict(t=68, r=64, b=52))


def linea_anual_pct(
    df: pd.DataFrame,
    title: str = "Participación anual respecto al total nacional",
) -> go.Figure:
    df = _prepare_anio(df)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["anio_hecho"].astype(int),
            y=df["pct_total"],
            mode="lines+markers",
            line=dict(width=3, color=COLOR_PRIMARY),
            marker=dict(size=8, color=COLOR_PRIMARY),
            hovertemplate="<b>Año %{x}</b><br>Participación: %{y:.1f}%<extra></extra>",
        )
    )
    _eje_anio(fig, df["anio_hecho"])
    fig.update_layout(
        title=title,
        xaxis_title="Año",
        yaxis_title="Participación del total (%)",
        hovermode="x unified",
    )
    ymax = float(df["pct_total"].max()) if len(df) else 1.0
    _fit_outside_text(fig, ymax, axis="y", padding=0.12)
    return _layout(fig, margin=dict(t=68, r=64, b=52))


def barras_horizontales(
    df: pd.DataFrame,
    y_col: str,
    x_col: str = "casos",
    title: str = "",
    pct_col: str | None = None,
    height: int | None = None,
) -> go.Figure:
    df = df.sort_values(x_col, ascending=True).copy()
    labels = df[y_col].astype(str)
    if pct_col and pct_col in df.columns:
        labels = labels + " (" + df[pct_col].round(1).astype(str) + "%)"
    
    if x_col == "tasa":
        hover = "<b>%{y}</b><br>Tasa: %{x:,.1f} por 100k hab.<br><extra></extra>"
        text_vals = df[x_col].map(lambda v: f"{v:,.1f}")
        x_title = "Tasa por 100.000 habitantes"
    else:
        hover = (
            "<b>%{y}</b><br>Casos: %{x:,}<br>"
            + ("Participación: %{customdata:.1f}%<br>" if pct_col else "")
            + "<extra></extra>"
        )
        text_vals = df[x_col].map(lambda v: f"{int(v):,}")
        x_title = "Casos registrados"

    custom = df[pct_col] if pct_col and pct_col in df.columns else None
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df[x_col],
            y=labels,
            orientation="h",
            marker_color=COLOR_PRIMARY,
            text=text_vals,
            textposition="outside",
            customdata=custom,
            hovertemplate=hover,
        )
    )
    fig.update_layout(title=title, xaxis_title=x_title, yaxis_title="")
    fig_height = height if height is not None else max(400, len(df) * 36)
    xmax = float(df[x_col].max()) if len(df) else 1.0
    _fit_outside_text(fig, xmax, axis="x")
    return _layout(fig, height=fig_height, margin=dict(l=56, r=88, t=60, b=52))


def barras_perfil_seleccion(
    df: pd.DataFrame,
    title: str = "Peso relativo por dimensión en la selección",
) -> go.Figure:
    plot = df.loc[~df["dimension"].isin(["Años", "Territorio"])].copy()
    plot = plot.sort_values("pct_seleccion", ascending=True)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=plot["pct_seleccion"],
            y=plot["dimension"],
            orientation="h",
            marker_color=COLOR_PRIMARY,
            text=plot["pct_seleccion"].map(lambda v: f"{v:.1f}%"),
            textposition="outside",
            customdata=plot[["detalle", "casos"]].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>%{customdata[0]}<br>"
                "Casos: %{customdata[1]:,}<br>"
                "% de la selección: %{x:.1f}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="% de la selección filtrada",
        yaxis_title="",
    )
    height = max(420, len(plot) * 38)
    xmax = float(plot["pct_seleccion"].max()) if len(plot) else 1.0
    _fit_outside_text(fig, xmax, axis="x")
    return _layout(fig, height=height, margin=dict(l=56, r=88, t=60, b=52))


def barras_zona_pct(
    df: pd.DataFrame,
    title: str = "Proporción por zona del hecho",
) -> go.Figure:
    df = df.sort_values("pct", ascending=True).copy()
    colors = [
        COLOR_ZONA.get(str(z), PALETTE_CATEGORICAL[i % len(PALETTE_CATEGORICAL)])
        for i, z in enumerate(df["zona_hecho"])
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["pct"],
            y=df["zona_hecho"],
            orientation="h",
            marker_color=colors,
            text=df["pct"].map(lambda v: f"{v:.1f}%"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Participación: %{x:.1f}%<br>Casos: %{customdata:,}<extra></extra>",
            customdata=df["casos"],
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Participación en la selección (%)",
        yaxis_title="Zona del hecho",
    )
    xmax = float(df["pct"].max()) if len(df) else 1.0
    _fit_outside_text(fig, xmax, axis="x")
    return _layout(fig, height=320, margin=dict(l=56, r=88, t=60, b=52))


def barras_municipios(
    df: pd.DataFrame,
    title: str = "Municipios con más casos en el departamento",
    label_col: str = "municipio_hecho",
) -> go.Figure:
    return barras_horizontales(
        df.head(5),
        label_col,
        title=title,
        pct_col=None,
    )


def _ordenar_categorias(valores, orden: list[str]) -> list:
    presentes = [v for v in orden if v in valores]
    extra = [v for v in valores if v not in orden]
    return presentes + sorted(extra, key=str)


def _color_por_grupo_edad(grupos: list) -> dict[str, str]:
    """Color fijo y claramente distinto por grupo etario (sin repetir tonos)."""
    colores: dict[str, str] = {}
    for g in grupos:
        etiqueta = str(g)
        if etiqueta == "Sin informacion":
            colores[etiqueta] = "#94A3B8"
            continue
        if etiqueta in EDAD_QUINQUENAL_ORDEN:
            idx = EDAD_QUINQUENAL_ORDEN.index(etiqueta)
        else:
            idx = len(colores) % len(PALETA_GRUPO_EDAD)
        colores[etiqueta] = PALETA_GRUPO_EDAD[idx % len(PALETA_GRUPO_EDAD)]
    return colores


def barras_apiladas_pct(
    df: pd.DataFrame,
    title: str = "Perfil de víctimas por sexo y edad",
) -> go.Figure:
    pivot = df.pivot_table(
        index="sexo_victima",
        columns="grupo_edad_quinquenal",
        values="casos",
        aggfunc="sum",
        fill_value=0,
    )
    cols = _ordenar_categorias(pivot.columns, EDAD_QUINQUENAL_ORDEN)
    pivot = pivot[cols]
    filas = _ordenar_categorias(pivot.index, SEXO_ORDEN)
    pivot = pivot.reindex(filas)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    colores = _color_por_grupo_edad(list(pct.columns))
    fig = go.Figure()
    for col in pct.columns:
        etiqueta = str(col)
        fig.add_trace(
            go.Bar(
                name=etiqueta,
                x=pct.index,
                y=pct[col],
                marker=dict(color=colores.get(etiqueta, "#94A3B8")),
                legendgroup=etiqueta,
                showlegend=True,
                hovertemplate=f"<b>{col}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="stack",
        title=title,
        yaxis_title="Porcentaje dentro de cada sexo (%)",
        xaxis_title="Sexo de la víctima",
        legend_title="Grupo etario",
        colorway=PALETA_GRUPO_EDAD,
    )
    fig = _layout(fig, height=560)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="center",
            x=0.5,
            tracegroupgap=10,
            font=dict(size=12),
        ),
        margin=dict(l=56, r=56, t=60, b=96, pad=4),
    )
    fig.update_yaxes(range=[0, 108])
    return fig


def _rango_y_pct(
    max_val: float, *, outside_labels: bool = False
) -> tuple[float, float]:
    """Límites del eje Y según el valor máximo observado (evita barras miniatura)."""
    if max_val <= 0:
        return 0.0, 10.0
    colchon = 0.22 if outside_labels else 0.1
    tope = max(max_val * (1 + colchon), max_val + (3.0 if outside_labels else 1.5))
    return 0.0, min(100.0, tope)


def _ordenar_ciclo(df: pd.DataFrame) -> pd.DataFrame:
    orden = [c for c in CICLO_ORDEN if c in df["ciclo_vital"].values]
    extra = [c for c in df["ciclo_vital"].unique() if c not in orden]
    df = df.copy()
    df["ciclo_vital"] = pd.Categorical(
        df["ciclo_vital"], categories=orden + list(extra), ordered=True
    )
    return df.sort_values("ciclo_vital")


def barras_ciclo(
    df: pd.DataFrame,
    sexo_resaltar: str = "Ambos",
    title: str = "Distribución por ciclo vital",
) -> go.Figure:
    if sexo_resaltar == "Ambos":
        sub = df.groupby(["ciclo_vital", "sexo_victima"], as_index=False)["casos"].sum()
        sub = _ordenar_ciclo(sub)
        pivot = sub.pivot(
            index="ciclo_vital", columns="sexo_victima", values="casos"
        ).fillna(0)
        ciclos = _ordenar_categorias(pivot.index, CICLO_ORDEN)
        pivot = pivot.reindex(ciclos)
        total = float(pivot.values.sum())
        fig = go.Figure()
        for sexo, color in (("Hombre", COLOR_MASCULINO), ("Mujer", COLOR_FEMENINO)):
            if sexo not in pivot.columns:
                continue
            casos = pivot[sexo]
            pct = casos / total * 100 if total else 0
            fig.add_trace(
                go.Bar(
                    name=sexo,
                    x=pivot.index.astype(str),
                    y=pct,
                    marker_color=color,
                    text=pct.map(lambda v: f"{v:.1f}%" if v >= 3 else ""),
                    textposition="inside",
                    insidetextanchor="middle",
                    hovertemplate=(
                        f"<b>{sexo}</b><br>%{{x}}<br>"
                        "Participación: %{y:.1f}%<br>Casos: %{customdata:,}<extra></extra>"
                    ),
                    customdata=casos.astype(int),
                )
            )
        fig.update_layout(barmode="stack", legend_title="Sexo")
        pct_pivot = pivot / total * 100 if total else pivot * 0
        ymax = float(pct_pivot.sum(axis=1).max()) if len(pct_pivot) else 0.0
        y0, y1 = _rango_y_pct(ymax, outside_labels=False)
        fig.update_yaxes(range=[y0, y1])
    else:
        sub = (
            df[df["sexo_victima"] == sexo_resaltar]
            .groupby("ciclo_vital", as_index=False)["casos"]
            .sum()
        )
        sub = _ordenar_ciclo(sub)
        total = sub["casos"].sum()
        sub["pct"] = sub["casos"] / total * 100 if total else 0
        color = COLOR_MASCULINO if sexo_resaltar == "Hombre" else COLOR_FEMENINO
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=sub["ciclo_vital"].astype(str),
                y=sub["pct"],
                marker_color=color,
                text=sub["pct"].map(lambda v: f"{v:.1f}%"),
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Participación: %{y:.1f}%<br>Casos: %{customdata:,}<extra></extra>",
                customdata=sub["casos"],
            )
        )
        ymax = float(sub["pct"].max()) if len(sub) else 0.0
    fig.update_layout(
        title=title,
        xaxis_title="Ciclo vital",
        yaxis_title="Participación (%)",
        xaxis_tickangle=-25,
    )
    if sexo_resaltar != "Ambos":
        y0, y1 = _rango_y_pct(ymax, outside_labels=True)
        fig.update_yaxes(range=[y0, y1])
        return _layout(fig, height=400, margin=dict(l=56, r=56, t=72, b=88))
    return _layout(fig, height=400, margin=dict(l=56, r=56, t=60, b=88))


SEVERIDAD_ORDEN = [
    "Sin incapacidad",
    "1 a 30",
    "31 a 90",
    "Más de 90",
    "Sin informacion",
]


def barras_severidad(
    df: pd.DataFrame,
    title: str = "Gravedad medicolegal (días de incapacidad)",
    height: int | None = None,
) -> go.Figure:
    plot = df.copy()
    orden = [s for s in SEVERIDAD_ORDEN if s in plot["categoria"].values]
    extra = [c for c in plot["categoria"] if c not in orden]
    plot["categoria"] = pd.Categorical(
        plot["categoria"], categories=orden + extra, ordered=True
    )
    plot = plot.sort_values("categoria")
    return barras_horizontales(
        plot, "categoria", title=title, pct_col="pct", height=height
    )


def barras_escenarios(
    df: pd.DataFrame,
    title: str = "Escenarios del hecho más frecuentes",
) -> go.Figure:
    return barras_horizontales(
        df.sort_values("casos", ascending=False).head(8),
        "categoria",
        title=title,
        pct_col="pct",
    )


def barras_top_franjas(
    df: pd.DataFrame,
    top_n: int = 5,
    title: str = "Combinaciones día-franja con más casos",
) -> go.Figure:
    plot = df.copy()
    plot["rango_hora"] = plot["rango_hora"].map(normalizar_franja)
    plot["combinacion"] = (
        plot["dia_hecho"].astype(str) + " · " + plot["rango_hora"].astype(str)
    )
    plot = plot.groupby("combinacion", as_index=False)["casos"].sum()
    plot = plot.nlargest(top_n, "casos")
    return barras_horizontales(plot, "combinacion", title=title)


def norm_depto_geo_key(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name).strip())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


POBLACION_DEPARTAMENTOS = {
    "amazonas": 79020,
    "antioquia": 6677930,
    "arauca": 294206,
    "archipielago de san andres providencia y santa catalina": 63786,
    "atlantico": 2722128,
    "bogota d c": 7743955,
    "santafe de bogota d c": 7743955,
    "bolivar": 2180976,
    "boyaca": 1242731,
    "caldas": 1018453,
    "caqueta": 410521,
    "casanare": 435195,
    "cauca": 1491937,
    "cesar": 1295387,
    "choco": 544916,
    "cundinamarca": 3242999,
    "cordoba": 1828947,
    "guainia": 50636,
    "guaviare": 86720,
    "huila": 1122622,
    "la guajira": 965718,
    "magdalena": 1426926,
    "meta": 1063200,
    "narino": 1627589,
    "norte de santander": 1620318,
    "putumayo": 359127,
    "quindio": 555401,
    "risaralda": 961055,
    "santander": 2280908,
    "sucre": 943874,
    "tolima": 1339998,
    "valle del cauca": 4532152,
    "vaupes": 44712,
    "vichada": 112958
}


def _geo_depto_lookup(geojson: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for feature in geojson.get("features", []):
        nombre = feature.get("properties", {}).get("NOMBRE_DPT")
        if nombre:
            lookup[norm_depto_geo_key(nombre)] = nombre
    return lookup


def _map_departamento_geo(
    departamento: str, lookup: dict[str, str]
) -> str | None:
    if departamento == DEPTO_BOGOTA:
        return lookup.get(norm_depto_geo_key("SANTAFE DE BOGOTA D.C"))
    return lookup.get(norm_depto_geo_key(departamento))


def _geo_departamentos(geojson: dict) -> list[str]:
    return sorted(
        feat["properties"]["NOMBRE_DPT"]
        for feat in geojson.get("features", [])
        if feat.get("properties", {}).get("NOMBRE_DPT")
    )


def _intensidad_anual(casos: pd.Series) -> pd.Series:
    out = pd.Series(0.0, index=casos.index, dtype=float)
    pos = casos > 0
    if pos.any():
        out.loc[pos] = casos.loc[pos].rank(pct=True, method="average")
    return out


def _completar_mapa_departamentos(
    plot: pd.DataFrame,
    geojson: dict,
    year_min: int,
    year_max: int,
    metric: str = "casos",
) -> pd.DataFrame:
    """Todos los departamentos del GeoJSON en cada año (casos=0 si no hay filtro)."""
    deptos = _geo_departamentos(geojson)
    years = list(range(int(year_min), int(year_max) + 1))
    grid = pd.MultiIndex.from_product(
        [deptos, years], names=["geo_depto", "anio_hecho"]
    ).to_frame(index=False)
    if plot.empty:
        agg = pd.DataFrame(columns=["geo_depto", "anio_hecho", "casos"])
    else:
        agg = plot.groupby(["geo_depto", "anio_hecho"], as_index=False)["casos"].sum()
    complete = grid.merge(agg, on=["geo_depto", "anio_hecho"], how="left")
    complete["casos"] = complete["casos"].fillna(0).astype(int)
    
    if metric == "tasa":
        complete["norm_key"] = complete["geo_depto"].map(norm_depto_geo_key)
        complete["poblacion"] = complete["norm_key"].map(POBLACION_DEPARTAMENTOS)
        complete["tasa"] = (complete["casos"] / complete["poblacion"]) * 100000
        complete["tasa"] = complete["tasa"].fillna(0.0)
        complete["intensidad"] = complete.groupby("anio_hecho")["tasa"].transform(
            _intensidad_anual
        )
    else:
        complete["intensidad"] = complete.groupby("anio_hecho")["casos"].transform(
            _intensidad_anual
        )
        
    complete["anio_hecho"] = complete["anio_hecho"].astype(int)
    return complete


def mapa_colombia_timeline(
    df: pd.DataFrame,
    geojson: dict,
    year_min: int,
    year_max: int,
    metric: str = "casos",
) -> go.Figure:
    """Mapa coroplético por departamento con animación anual."""
    lookup = _geo_depto_lookup(geojson)
    deptos_geo = _geo_departamentos(geojson)
    if not deptos_geo:
        return _layout(go.Figure(), height=480)

    if df.empty:
        plot = _completar_mapa_departamentos(df, geojson, year_min, year_max, metric=metric)
    else:
        plot = df.copy()
        plot["anio_hecho"] = pd.to_numeric(plot["anio_hecho"], errors="coerce")
        plot = plot.dropna(subset=["anio_hecho"])
        plot = plot[
            (plot["anio_hecho"] >= year_min) & (plot["anio_hecho"] <= year_max)
        ].copy()
        plot["geo_depto"] = plot["departamento_hecho"].map(
            lambda d: _map_departamento_geo(str(d), lookup)
        )
        plot = plot.dropna(subset=["geo_depto"])
        plot = _completar_mapa_departamentos(plot, geojson, year_min, year_max, metric=metric)

    if plot.empty:
        return _layout(go.Figure(), height=480)

    color_col = "tasa" if metric == "tasa" else "casos"
    fig = px.choropleth(
        plot,
        geojson=geojson,
        locations="geo_depto",
        featureidkey="properties.NOMBRE_DPT",
        color="intensidad",
        animation_frame="anio_hecho",
        animation_group="geo_depto",
        range_color=(0, 1),
        color_continuous_scale=MAP_CHOROPLETH_SCALE,
        custom_data=[color_col],
        labels={"intensidad": "Percentil en el año", color_col: "Tasa por 100k hab." if metric == "tasa" else "Casos"},
        title="Tasa de casos por 100.000 habitantes por departamento" if metric == "tasa" else "Casos registrados por departamento",
    )
    fig.update_geos(
        fitbounds="geojson",
        visible=False,
        showframe=False,
        showcoastlines=False,
        lataxis_range=[-4.5, 13.5],
        lonaxis_range=[-79.5, -66.5],
        domain=dict(x=[0.0, 1.0], y=[0.22, 1.0]),
    )
    if metric == "tasa":
        hover_tpl = (
            "<b>%{{location}}</b><br>Año: {year}<br>"
            "Tasa: %{{customdata[0]:,.1f}} por 100k hab.<extra></extra>"
        )
    else:
        hover_tpl = (
            "<b>%{{location}}</b><br>Año: {year}<br>"
            "Casos: %{{customdata[0]:,}}<extra></extra>"
        )
        
    if fig.frames:
        for frame in fig.frames:
            frame.data[0].hovertemplate = hover_tpl.format(year=frame.name)
        fig.update(data=fig.frames[0].data)
    else:
        if metric == "tasa":
            fig.update_traces(
                hovertemplate="<b>%{location}</b><br>Tasa: %{z:,.1f} por 100k hab.<extra></extra>"
            )
        else:
            fig.update_traces(
                hovertemplate="<b>%{location}</b><br>Casos: %{z:,}<extra></extra>"
            )
    fig.update_coloraxes(
        colorbar=dict(
            orientation="h",
            title=dict(text="Percentil en el año", side="bottom", font=dict(size=11)),
            tickformat=".0%",
            len=0.72,
            thickness=10,
            x=0.14,
            xanchor="left",
            y=0.165,
            yanchor="middle",
            ticklen=3,
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=36, b=0),
        dragmode=False,
        uirevision="mapa-colombia-timeline",
    )
    if fig.layout.sliders:
        slider = fig.layout.sliders[0]
        slider.len = 0.92
        slider.x = 0.04
        slider.xanchor = "left"
        slider.y = 0.0
        slider.yanchor = "bottom"
        slider.pad.t = 16
        slider.pad.b = 0
        slider.pad.l = 0
        slider.pad.r = 0
        slider.currentvalue.prefix = "Año: "
        slider.currentvalue.font.size = 11
    return _layout(fig, height=580, margin=dict(l=0, r=0, t=40, b=0))


def heatmap_dia_hora(
    df: pd.DataFrame,
    title: str = "Incidencia por día de la semana y franja horaria",
) -> go.Figure:
    if df.empty:
        return _layout(go.Figure())
    plot = df.copy()
    plot["rango_hora"] = plot["rango_hora"].map(normalizar_franja)
    pivot = plot.pivot_table(
        index="dia_hecho",
        columns="rango_hora",
        values="casos",
        aggfunc="sum",
        fill_value=0,
    )
    present_dias = [d for d in DIAS_ORDEN if d in pivot.index]
    pivot = pivot.reindex(present_dias if present_dias else pivot.index)
    cols = [c for c in FRANJAS_ORDEN if c in pivot.columns]
    extra = [c for c in pivot.columns if c not in FRANJAS_ORDEN]
    pivot = pivot[cols + list(extra)]
    fig = px.imshow(
        pivot,
        aspect="auto",
        title=title,
        color_continuous_scale=HEATMAP_SCALE,
        labels=dict(x="Franja horaria", y="Día de la semana", color="Casos"),
    )
    fig.update_traces(
        hovertemplate="Día: %{y}<br>Franja: %{x}<br>Casos: %{z:,}<extra></extra>"
    )
    fig.update_layout(xaxis_tickangle=-30)
    fig.update_coloraxes(colorbar=dict(title="Casos", len=0.75, thickness=14, xpad=8))
    return _layout(fig, height=400, margin=dict(l=72, r=88, t=60, b=96))
