"""Auditoria de calidad Data Preparation (solo lectura)."""
from __future__ import annotations

import pandas as pd

from src.prepare import (
    MISSING_PATTERNS,
    _find_csv,
    _norm_text,
    _read_csv,
    _rename_columns,
)

COLS_DROP = [
    "contexto_hecho",
    "codigo_dane_municipio",
    "codigo_dane_departamento",
    "grupo_mayor_menor_edad",
    "grupo_edad_judicial",
    "dias_incapacidad",
    "orientacion_sexual",
    "identidad_genero",
    "transgenero",
    "pueblo_indigena",
    "tipo_discapacidad",
    "pertenencia_grupal",
    "pais_nacimiento",
]

OLAP_DIMS = {
    "anio_hecho",
    "departamento_hecho",
    "municipio_hecho",
    "localidad_hecho",
    "sexo_victima",
    "grupo_edad_quinquenal",
    "ciclo_vital",
    "zona_hecho",
    "pertenencia_etnica",
    "escenario_hecho",
    "mecanismo_causal",
    "severidad_categoria",
    "presunto_agresor",
    "dia_hecho",
    "rango_hora",
}

CLUSTER_COLS = {
    "sexo_victima",
    "grupo_edad_quinquenal",
    "ciclo_vital",
    "zona_hecho",
    "escenario_hecho",
    "mecanismo_causal",
    "presunto_agresor",
    "departamento_hecho",
}

ARTICLE_COLS = {
    "anio_hecho",
    "departamento_hecho",
    "severidad_categoria",
}


def miss_rate(s: pd.Series) -> float:
    if s.dtype == bool:
        return float(s.isna().mean() * 100)
    if pd.api.types.is_numeric_dtype(s):
        return float(s.isna().mean() * 100)
    return float(
        (s.isna() | s.astype(str).str.strip().eq("Sin informacion")).mean() * 100
    )


def raw_missing_profile(raw: pd.DataFrame) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for col in raw.columns:
        s = raw[col]
        if pd.api.types.is_numeric_dtype(s):
            out[col] = {"na_pct": float(s.isna().mean() * 100), "pattern_pct": 0.0}
        else:
            norm = s.map(_norm_text)
            out[col] = {
                "na_pct": float(s.isna().mean() * 100),
                "pattern_pct": float(norm.isin(MISSING_PATTERNS).mean() * 100),
            }
    return out


def casefold_duplicates(series: pd.Series) -> dict[str, list[str]]:
    s = series.dropna().astype(str)
    s = s[s != "Sin informacion"]
    grouped: dict[str, list[str]] = {}
    for val in s.unique():
        key = val.casefold()
        grouped.setdefault(key, []).append(val)
    return {k: v for k, v in grouped.items() if len(v) > 1}


def main() -> None:
    raw = _rename_columns(_read_csv(_find_csv()))
    prepared = pd.read_parquet("data/processed/dataset.parquet")
    raw_miss = raw_missing_profile(raw)

    print("=== INVENTARIO ===")
    print(f"RAW cols: {len(raw.columns)}")
    print(f"PREPARED cols: {len(prepared.columns)}")
    print(f"DROPPED: {len(COLS_DROP)}")

    print("\n=== COLUMNAS ELIMINADAS (evidencia cruda) ===")
    for col in COLS_DROP:
        if col not in raw.columns:
            continue
        nu = raw[col].nunique()
        top = raw[col].value_counts(dropna=False).head(3)
        rb = raw_miss[col]
        top_str = "; ".join(f"{k!r}={int(v)}" for k, v in top.items())
        print(
            f"{col} | nunique={nu} | na={rb['na_pct']:.2f}% | "
            f"pat_missing={rb['pattern_pct']:.2f}% | top: {top_str}"
        )

    print("\n=== FALTANTES ANTES vs DESPUES (columnas exportadas) ===")
    print("columna | raw_na% | raw_pat% | after_miss% | nunique")
    for col in prepared.columns:
        rb = raw_miss.get(col, {"na_pct": 0.0, "pattern_pct": 0.0})
        print(
            f"{col} | {rb['na_pct']:.2f} | {rb['pattern_pct']:.2f} | "
            f"{miss_rate(prepared[col]):.2f} | {prepared[col].nunique()}"
        )

    print("\n=== TIPOS FINALES ===")
    for col in prepared.columns:
        print(f"{col}: {prepared[col].dtype}")

    print("\n=== RANGOS E INCONSISTENCIAS ===")
    print(
        f"anio_hecho: min={prepared['anio_hecho'].min()} max={prepared['anio_hecho'].max()} "
        f"nulls={prepared['anio_hecho'].isna().sum()}"
    )
    print(
        f"id: unique={prepared['id'].nunique()} dup={prepared['id'].duplicated().sum()}"
    )
    print(f"mes_hecho ({prepared['mes_hecho'].nunique()}): {sorted(prepared['mes_hecho'].unique())}")
    print(f"dia_hecho ({prepared['dia_hecho'].nunique()}): {sorted(prepared['dia_hecho'].unique())}")
    print(
        f"severidad: {prepared['severidad_categoria'].value_counts().to_dict()}"
    )
    print(
        f"dias_incapacidad_num: {prepared['dias_incapacidad_num'].value_counts(dropna=False).to_dict()}"
    )
    print(f"fin_semana: {prepared['fin_semana'].value_counts().to_dict()}")

    print("\n=== DUPLICADOS CASEFOLD RESIDUALES ===")
    check_cols = [
        "escenario_hecho",
        "presunto_agresor",
        "mecanismo_causal",
        "zona_hecho",
        "departamento_hecho",
        "municipio_hecho",
        "circunstancia_detallada",
        "sexo_agresor",
        "escolaridad",
        "estado_civil",
        "pertenencia_etnica",
        "actividad_hecho",
        "diagnostico_topografico",
        "rango_hora",
    ]
    for col in check_cols:
        if col not in prepared.columns:
            continue
        dups = casefold_duplicates(prepared[col])
        if dups:
            print(f"{col}: {len(dups)} grupos casefold duplicados")
            for labels in list(dups.values())[:3]:
                counts = prepared[col].value_counts()
                detail = ", ".join(f"{l}={int(counts.get(l, 0))}" for l in labels)
                print(f"  {detail}")

    print("\n=== ESCENARIO fragmentacion residual ===")
    esc = prepared["escenario_hecho"].value_counts()
    for label, n in esc.items():
        low = str(label).lower()
        if "administraci" in low or "vía" in low or "via" in low or "calle" in low:
            print(f"  {int(n):>8} | {label!r}")

    print("\n=== USO POR COMPONENTE (26 columnas exportadas) ===")
    print("columna | OLAP | Cluster | Articulo(fig) | Dashboard | Nota")
    dashboard_only = OLAP_DIMS  # dashboard consume agregados OLAP
    for col in prepared.columns:
        olap = col in OLAP_DIMS or col == "severidad_categoria"
        cluster = col in CLUSTER_COLS
        article = col in ARTICLE_COLS
        # derived used indirectly
        if col == "severidad_categoria":
            olap = True
            article = True
        if col == "id":
            note = "trazabilidad offline"
        elif col in {"anio_mes", "fin_semana", "dias_incapacidad_num"}:
            note = "derivada sin consumo"
        elif col in {"escolaridad", "estado_civil", "actividad_hecho", "circunstancia_detallada", "diagnostico_topografico", "sexo_agresor"}:
            note = "conservada sin agregado"
        elif col == "mes_hecho":
            note = "canonizada pero sin agregado mensual"
        else:
            note = ""
        dash = col in dashboard_only or col in {"severidad_categoria"}
        print(
            f"{col} | {olap} | {cluster} | {article} | {dash} | {note}"
        )

    unused = [
        c
        for c in prepared.columns
        if c not in OLAP_DIMS
        and c not in CLUSTER_COLS
        and c not in ARTICLE_COLS
        and c != "id"
    ]
    print("\n=== SIN USO EN OLAP/CLUSTER/ARTICULO ===")
    print(unused)

    derived_unused = [c for c in ["anio_mes", "fin_semana", "dias_incapacidad_num"] if c in prepared.columns]
    print("\n=== DERIVADAS SIN CONSUMO ===")
    for c in derived_unused:
        in_olap = c in OLAP_DIMS
        print(f"{c}: olap={in_olap}")

    # DANE redundancy evidence
    if "codigo_dane_departamento" in raw.columns:
        pairs = raw.groupby(["codigo_dane_departamento", "departamento_hecho"]).ngroups
        print(f"\n=== REDUNDANCIA DANE dept code-name pairs: {pairs} ===")

    # Age semantic redundancy
    if "grupo_mayor_menor_edad" in raw.columns:
        cross = raw.groupby(["grupo_mayor_menor_edad", "ciclo_vital"]).size()
        print(f"\n=== grupo_mayor x ciclo combinations: {len(cross)} ===")


if __name__ == "__main__":
    main()
