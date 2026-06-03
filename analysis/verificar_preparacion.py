"""Verificacion reproducible de calidad post-prepare (evidencia para sustentacion)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prepare import (
    COLS_TO_DROP,
    COLUMN_RENAME_MAP,
    DATASET_CSV,
    DATASET_PARQUET,
    _find_csv,
    _read_csv,
    _rename_columns,
)

# Columnas donde la auditoria documento homologacion explicita
COLS_HOMOLOG_AUDITADAS = [
    "pertenencia_etnica",
    "escenario_hecho",
    "sexo_agresor",
    "escolaridad",
    "estado_civil",
    "actividad_hecho",
]

DERIVED_COLS = [
    "severidad_categoria",
    "dias_incapacidad_num",
    "anio_mes",
    "fin_semana",
]


def casefold_duplicate_groups(series: pd.Series) -> dict[str, list[str]]:
    s = series.dropna().astype(str)
    s = s[s != "Sin informacion"]
    groups: dict[str, set[str]] = {}
    for val in s.unique():
        key = val.casefold()
        groups.setdefault(key, set()).add(val)
    return {k: sorted(v) for k, v in groups.items() if len(v) > 1}


def main() -> None:
    raw_path = _find_csv()
    raw = _rename_columns(_read_csv(raw_path))
    pq = pd.read_parquet(DATASET_PARQUET)
    csv_path = DATASET_CSV
    csv_ok = csv_path.exists()
    csv_df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False) if csv_ok else None

    print("=== VERIFICACION", datetime.now(timezone.utc).isoformat(), "===")
    print(f"Fuente: {raw_path.name}")
    print(f"Filas crudo (renombrado): {len(raw):,}")
    print(f"Filas parquet: {len(pq):,}")
    if csv_ok and csv_df is not None:
        print(f"Filas dataset_limpio.csv: {len(csv_df):,}")
        print(f"Columnas parquet vs csv: {len(pq.columns)} vs {len(csv_df.columns)}")
        print(f"Misma forma: {pq.shape == csv_df.shape}")
        print(f"Columnas iguales: {list(pq.columns) == list(csv_df.columns)}")

    filas_perdidas = len(raw) - len(pq)
    print(f"Filas excluidas por filtro anio o transformacion: {filas_perdidas:,}")

    # Casefold en columnas auditadas
    print("\n=== CASEFOLD DUPLICADOS (columnas homologacion auditadas) ===")
    total_grupos = 0
    for col in COLS_HOMOLOG_AUDITADAS:
        if col not in pq.columns:
            print(f"{col}: NO EN PARQUET")
            continue
        dups = casefold_duplicate_groups(pq[col])
        total_grupos += len(dups)
        print(f"{col}: {len(dups)} grupos casefold con >1 etiqueta")
        for labels in list(dups.values())[:3]:
            print(f"  {labels}")

    # Otras categóricas (pueden tener varias etiquetas INMLCF legitimas)
    print("\n=== CASEFOLD DUPLICADOS (otras categóricas exportadas) ===")
    otras = [c for c in pq.columns if c not in COLS_HOMOLOG_AUDITADAS and pq[c].dtype == object]
    for col in otras:
        dups = casefold_duplicate_groups(pq[col])
        if dups:
            print(f"{col}: {len(dups)} grupos (ej. {list(dups.values())[:1]})")

    print("\n=== RESUMEN CONSERVADOR ===")
    print(
        f"En {len(COLS_HOMOLOG_AUDITADAS)} columnas de homologacion documentada: "
        f"{total_grupos} grupos casefold con mas de una etiqueta."
    )
    if total_grupos == 0:
        print(
            "Interpretacion: no se detectaron duplicados ortograficos residuales "
            "en esas columnas en el artefacto actual."
        )
    else:
        print("Interpretacion: persisten variantes ortograficas; revisar canonizacion.")

    out = PROJECT_ROOT / "data" / "processed" / "verificacion_preparacion.json"
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "filas_raw": len(raw),
        "filas_parquet": len(pq),
        "columnas_raw": len(raw.columns),
        "columnas_parquet": len(pq.columns),
        "cols_dropped": COLS_TO_DROP,
        "cols_derived": DERIVED_COLS,
        "casefold_grupos_columnas_auditadas": {
            c: len(casefold_duplicate_groups(pq[c]))
            for c in COLS_HOMOLOG_AUDITADAS
            if c in pq.columns
        },
        "parquet_csv_misma_forma": bool(
            csv_ok and csv_df is not None and pq.shape == csv_df.shape
        ),
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON: {out}")


if __name__ == "__main__":
    main()
