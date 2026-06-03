"""Perfilado para decisiones de homologacion y faltantes (solo lectura)."""
from __future__ import annotations

import pandas as pd

from src.prepare import MISSING_PATTERNS, _norm_text, _read_csv, _find_csv, _rename_columns

COLS_HOMOLOG = [
    "pertenencia_etnica",
    "escenario_hecho",
    "sexo_agresor",
    "escolaridad",
    "estado_civil",
    "actividad_hecho",
]

# Candidatos institucionales a faltante (normalizados)
MISSING_CANDIDATES = [
    "no sabe / no informa",
    "no sabe/no informa",
    "no registra",
    "no reporta",
    "no reportado",
    "ninguno",
    "ninguna",
    "sin dato",
    "sin registro",
    "no habia sido implementada",
    "no había sido implementada",
    "no aplica",
    "no definido",
    "desconocido",
    "ignorado",
    "999",
    "sin informacion",
    "sin información",
]


def casefold_groups(series: pd.Series) -> dict[str, list[tuple[str, int]]]:
    vc = series.value_counts(dropna=False)
    groups: dict[str, list[tuple[str, int]]] = {}
    for label, n in vc.items():
        if pd.isna(label):
            key = "__na__"
        else:
            key = str(label).casefold()
        groups.setdefault(key, []).append((str(label), int(n)))
    return {k: v for k, v in groups.items() if len(v) > 1}


def candidate_missing_rates(raw: pd.DataFrame) -> None:
    print("\n=== CANDIDATOS FALTANTE POR COLUMNA (freq > 0) ===")
    for col in raw.columns:
        if pd.api.types.is_numeric_dtype(raw[col]):
            continue
        norm = raw[col].map(_norm_text)
        hits: list[tuple[str, int]] = []
        for cand in MISSING_CANDIDATES:
            n = int(norm.eq(cand).sum())
            if n > 0:
                hits.append((cand, n))
        if not hits:
            continue
        hits.sort(key=lambda x: -x[1])
        total = len(raw)
        line = "; ".join(f"{c}={n} ({n/total*100:.2f}%)" for c, n in hits[:8])
        already = int(norm.isin(MISSING_PATTERNS).sum())
        print(f"{col} | already_in_MISSING_PATTERNS={already} | {line}")


def homolog_evidence(raw: pd.DataFrame) -> None:
    print("\n=== FRAGMENTACION CASEFOLD (grupos con >1 etiqueta) ===")
    for col in COLS_HOMOLOG:
        if col not in raw.columns:
            continue
        groups = casefold_groups(raw[col])
        print(f"\n--- {col} ({len(groups)} grupos) ---")
        for key, labels in sorted(groups.items(), key=lambda x: -sum(n for _, n in x[1]))[:15]:
            detail = ", ".join(f"{lbl!r}={n}" for lbl, n in sorted(labels, key=lambda x: -x[1]))
            print(f"  [{key}] -> {detail}")


def dropped_cols_stats(raw: pd.DataFrame) -> None:
    drops = [
        "orientacion_sexual",
        "identidad_genero",
        "transgenero",
        "pueblo_indigena",
        "tipo_discapacidad",
        "pertenencia_grupal",
        "pais_nacimiento",
        "contexto_hecho",
    ]
    print("\n=== COLUMNAS ELIMINADAS (top categorias) ===")
    for col in drops:
        if col not in raw.columns:
            continue
        vc = raw[col].value_counts(dropna=False).head(5)
        print(f"{col} nunique={raw[col].nunique()}")
        for k, v in vc.items():
            print(f"  {k!r}: {int(v)} ({int(v)/len(raw)*100:.2f}%)")


def main() -> None:
    raw = _rename_columns(_read_csv(_find_csv()))
    print(f"Filas: {len(raw):,}")
    homolog_evidence(raw)
    candidate_missing_rates(raw)
    dropped_cols_stats(raw)


if __name__ == "__main__":
    main()
