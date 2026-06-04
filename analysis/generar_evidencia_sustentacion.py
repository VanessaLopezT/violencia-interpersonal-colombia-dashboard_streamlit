"""Genera tablas comparativas antes/despues para sustentacion Fase 3."""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prepare import (
    COLUMN_RENAME_MAP,
    MISSING_PATTERNS,
    YEAR_MAX,
    YEAR_MIN,
    _norm_text,
    _read_csv,
    _find_csv,
    _rename_columns,
)

OUT_DIR = PROJECT_ROOT / "docs" / "evidencia_sustentacion"
FILTER_COLS = [
    "departamento_hecho",
    "municipio_hecho",
    "sexo_victima",
    "zona_hecho",
    "pertenencia_etnica",
    "pertenencia_grupal",
    "ciclo_vital",
]
ACCENT_PUNCT_CHECK_COLS = {
    "departamento_hecho",
    "zona_hecho",
    "pertenencia_etnica",
    "pertenencia_grupal",
}


def _old_severidad_from_digits(value: object) -> str:
    """Replica erronea anterior: primer digito del texto."""
    if pd.isna(value):
        return "Sin informacion"
    text = _norm_text(value)
    digits = re.findall(r"\d+", str(text))
    if not digits:
        return "Sin informacion"
    dias = float(digits[0])
    if dias == 0:
        return "Sin incapacidad"
    if dias <= 5:
        return "Leve (1-5 dias)"
    if dias <= 15:
        return "Moderada (6-15 dias)"
    if dias <= 30:
        return "Alta (16-30 dias)"
    return "Muy alta (>30 dias)"


def _missing_stats(raw: pd.DataFrame, prep: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for col in prep.columns:
        raw_series = raw[col] if col in raw.columns else pd.Series(dtype=object)
        raw_na = float(raw_series.isna().mean() * 100)
        raw_pattern = 0.0
        if not pd.api.types.is_numeric_dtype(raw_series):
            norm = raw_series.map(_norm_text)
            raw_pattern = float(norm.isin(MISSING_PATTERNS).mean() * 100)
        prep_na = float(
            (prep[col].isna() | prep[col].astype(str).str.strip().eq("Sin informacion")).mean()
            * 100
        )
        rows.append(
            {
                "columna": col,
                "raw_na": raw_na,
                "raw_pat": raw_pattern,
                "prep_na": prep_na,
                "diff_na": raw_na - prep_na,
            }
        )
    return pd.DataFrame(rows).sort_values(["raw_na", "raw_pat"], ascending=False)


def _label_key(value: object, *, accent_punct: bool) -> str:
    text = str(value).strip()
    if not accent_punct:
        return text.casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).casefold().strip()


def _label_groups(series: pd.Series, *, accent_punct: bool = False) -> dict[str, list[str]]:
    s = series.dropna().astype(str)
    s = s[s != "Sin informacion"]
    groups: dict[str, set[str]] = {}
    for val in s.unique():
        key = _label_key(val, accent_punct=accent_punct)
        groups.setdefault(key, set()).add(val)
    return {k: sorted(v) for k, v in groups.items() if len(v) > 1}


def _top_values(series: pd.Series, n: int = 8) -> list[tuple[str, int]]:
    return [
        (str(k), int(v))
        for k, v in series.value_counts(dropna=False).head(n).items()
    ]


def _format_counts(rows: list[tuple[str, int]]) -> list[str]:
    return [f"| {label} | {count:,} |" for label, count in rows]


def _year_out_of_range(raw: pd.DataFrame) -> pd.Series:
    year = pd.to_numeric(raw["anio_hecho"], errors="coerce")
    return year.isna() | (year < YEAR_MIN) | (year > YEAR_MAX)


def _render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---" for _ in headers]) + "|")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def _render_list(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [title, "", ", ".join(items), ""]


def _render_section(title: str, lines: list[str]) -> list[str]:
    return [f"## {title}", "", *lines, ""]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = _rename_columns(_read_csv(_find_csv()))
    prep = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "dataset.parquet")

    dropped = [c for c in raw.columns if c not in prep.columns]
    derived = [c for c in prep.columns if c not in raw.columns]
    kept = [c for c in prep.columns if c in raw.columns]
    raw_outside = raw[_year_out_of_range(raw)]

    missing = _missing_stats(raw, prep)
    missing_rows = [
        [
            row["columna"],
            f"{row['raw_na']:.2f} %",
            f"{row['raw_pat']:.2f} %",
            f"{row['prep_na']:.2f} %",
        ]
        for _, row in missing.iterrows()
    ]

    lines: list[str] = [
        "# Evidencia comparativa — Data Preparation (CRISP-DM Fase 3)",
        "",
        f"Generado sobre fuente INMLCF con **{len(raw):,}** registros en CSV crudo renombrado "
        f"y **{len(prep):,}** registros en dataset preparado.",
        "",
        "## Flujo de datos",
        "",
        "```text",
        "CSV original (data/raw/)",
        "  -> lectura + renombrado (35 columnas)",
        "  -> limpieza y preparacion (src/prepare.py)",
        "  -> dataset_limpio.csv   (inspeccion / auditoria / Excel)",
        "  -> dataset.parquet      (formato principal del pipeline)",
        "  -> agregados OLAP (analysis/run.py)",
        "  -> dashboard Streamlit",
        "```",
        "",
        "## Comparacion fuente vs dataset preparado",
        "",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Filas CSV original (tras renombrar) | {len(raw):,} |",
        f"| Filas dataset final | {len(prep):,} |",
        f"| Filas excluidas por filtro 2015-2024 | {len(raw) - len(prep):,} |",
        f"| Filas con año inválido o fuera de rango | {len(raw_outside):,} |",
        f"| Columnas originales (CSV) | {len(raw.columns)} |",
        f"| Columnas finales exportadas | {len(prep.columns)} |",
        f"| Columnas eliminadas | {len(dropped)} |",
        f"| Columnas derivadas | {len(derived)} |",
        "",
        *(_render_list("### Columnas eliminadas", [f"`{c}`" for c in dropped])),
        *(_render_list("### Columnas derivadas", [f"`{c}`" for c in derived])),
        *(_render_list("### Columnas finales", [f"`{c}`" for c in prep.columns])),
    ]

    lines += [
        "## 1. Faltantes y patrones de limpieza",
        "",
        "| Columna | raw_na% | raw_pat% | prep_na% |",
        "|--------|--------:|--------:|--------:|",
    ]
    lines += ["| {} | {} | {} | {} |".format(*row) for row in missing_rows]
    lines += [
        "",
        "Las columnas anteriores muestran el impacto de la limpieza de faltantes: valores institucionales "
        "como 'Sin informacion' y variantes se recodifican antes de exportar el dataset preparado.",
        "",
    ]

    lines += [
        "## 2. Homologaciones clave",
        "",
        "Las siguientes dimensiones se homologan en `src/prepare.py` mediante normalizacion y canonizacion.",
        "",
    ]

    for col in [
        "departamento_hecho",
        "municipio_hecho",
        "zona_hecho",
        "pertenencia_etnica",
        "escenario_hecho",
        "sexo_agresor",
        "pertenencia_grupal",
    ]:
        if col not in raw.columns or col not in prep.columns:
            continue
        raw_top = _top_values(raw[col], n=6)
        prep_top = _top_values(prep[col], n=6)
        lines += [
            f"### {col}",
            "",
            f"Valores crudos en la fuente (top {len(raw_top)}):",
            "",
            "| Etiqueta | Casos |",
            "|--------|------:|",
            *(_format_counts(raw_top)),
            "",
            f"Valores preparados en el dataset final (top {len(prep_top)}):",
            "",
            "| Etiqueta | Casos |",
            "|--------|------:|",
            *(_format_counts(prep_top)),
            "",
        ]
        if col == "pertenencia_grupal":
            final_values = _top_values(prep[col], n=prep[col].nunique())
            lines += [
                "Modalidades finales completas de `pertenencia_grupal` tras homologacion:",
                "",
                "| Etiqueta final | Casos |",
                "|--------|------:|",
                *(_format_counts(final_values)),
                "",
            ]

    lines += [
        "## 3. Verificacion de limpieza en filtros usados",
        "",
        "Se revisan las columnas que alimentan los filtros del dashboard. Para departamentos, zona y pertenencias "
        "se detectan tambien diferencias por tildes, puntuacion o espacios; en municipios se conserva la etiqueta "
        "oficial para no mezclar municipios distintos que solo difieren por tilde.",
        "",
    ]

    for col in FILTER_COLS:
        if col not in raw.columns or col not in prep.columns:
            continue
        accent_punct = col in ACCENT_PUNCT_CHECK_COLS
        raw_groups = _label_groups(raw[col], accent_punct=accent_punct)
        prep_groups = _label_groups(prep[col], accent_punct=accent_punct)
        estado = "OK" if not prep_groups else "REVISAR"
        lines += [
            f"- {col}: {estado}. {len(raw_groups)} grupos duplicados visibles en raw vs {len(prep_groups)} en prepared.",
        ]
        if raw_groups:
            sample = list(raw_groups.items())[:3]
            for key, variants in sample:
                lines.append(f"  - {key}: {', '.join(repr(v) for v in variants)}")
        if prep_groups:
            sample = list(prep_groups.items())[:3]
            lines.append("  Ejemplos residuales en el preparado:")
            for key, variants in sample:
                lines.append(f"  - {key}: {', '.join(repr(v) for v in variants)}")
        lines.append("")

    lines += [
        "## 4. Severidad medicolegal",
        "",
        "Se corrige la heuristica anterior que solo tomaba el primer digito del texto de días de incapacidad.",
        "",
        "| Proceso | Categoria | Casos | % sobre el total |",
        "|--------|----------|------:|------------------:|",
    ]

    old_sev = raw["dias_incapacidad"].map(_old_severidad_from_digits).value_counts()
    new_sev = prep["severidad_categoria"].value_counts()
    for cat, n in old_sev.items():
        lines.append(f"| Antes | {cat} | {int(n):,} | {n / len(raw) * 100:.1f} % |")
    for cat, n in new_sev.items():
        lines.append(f"| Despues | {cat} | {int(n):,} | {n / len(prep) * 100:.1f} % |")
    lines += [
        "",
        "Esta comparacion demuestra la correccion de la categoria de severidad medicolegal antes "
        "y despues de la normalizacion en el pipeline.",
        "",
    ]

    lines += [
        "## 5. Columnas y flujo final",
        "",
        "- `data/processed/dataset_limpio.csv`: CSV de inspecton y auditoria con las mismas filas y columnas que el parquet.",
        "- `data/processed/dataset.parquet`: formato principal para analisis y agregados OLAP.",
        "- `analysis/verificar_preparacion.py`: script de verificacion reproducible y generacion de JSON de evidencia.",
        "",
        "### Recomendaciones para presentacion",
        "",
        "- Exportar el CSV limpio a Excel para mostrar tablas con filas y columnas auditadas.",
        "- Usar este markdown como respaldo tecnico de las transformaciones.",
    ]

    path = OUT_DIR / "comparacion_antes_despues.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidencia: {path}")


if __name__ == "__main__":
    main()
