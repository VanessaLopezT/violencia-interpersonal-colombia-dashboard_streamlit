"""Genera tablas comparativas antes/despues para sustentacion Fase 3."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.prepare import (
    MISSING_PATTERNS,
    _norm_text,
    _read_csv,
    _find_csv,
    _rename_columns,
)

OUT_DIR = PROJECT_ROOT / "docs" / "evidencia_sustentacion"
N = 981_611


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = _rename_columns(_read_csv(_find_csv()))
    prep = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "dataset.parquet")

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
        f"| Columnas originales (CSV) | 35 |",
        f"| Columnas eliminadas en prepare | 13 |",
        f"| Columnas derivadas anadidas | 4 |",
        f"| Columnas finales exportadas | {len(prep.columns)} |",
        "",
        "### Columnas eliminadas",
        "",
        "contexto_hecho, codigo_dane_municipio, codigo_dane_departamento, "
        "grupo_mayor_menor_edad, grupo_edad_judicial, dias_incapacidad, "
        "orientacion_sexual, identidad_genero, transgenero, pueblo_indigena, "
        "tipo_discapacidad, pertenencia_grupal, pais_nacimiento",
        "",
        "### Columnas derivadas",
        "",
        "severidad_categoria, dias_incapacidad_num, anio_mes, fin_semana",
        "",
        "### Columnas finales",
        "",
        ", ".join(f"`{c}`" for c in prep.columns),
        "",
    ]

    # 1 Homologacion pertenencia etnica
    etnia_raw = raw["pertenencia_etnica"].value_counts()
    etnia_prep = prep["pertenencia_etnica"].value_counts()
    lines += [
        "## 1. Homologacion — pertenencia etnica",
        "",
        "Variantes ortograficas del mismo concepto (CSV crudo):",
        "",
        "| Etiqueta en fuente | Casos |",
        "|---------------------|------:|",
    ]
    for label in ["Sin pertenencia étnica", "Sin Pertenencia Étnica", "ROM (Gitano)", "Rom (Gitano)"]:
        if label in etnia_raw.index:
            lines.append(f"| {label} | {int(etnia_raw[label]):,} |")
    lines += [
        "",
        "Tras preparacion (forma modal unificada):",
        "",
        "| Etiqueta | Casos |",
        "|----------|------:|",
    ]
    for label in ["Sin pertenencia étnica", "Sin informacion"]:
        if label in etnia_prep.index:
            lines.append(f"| {label} | {int(etnia_prep[label]):,} |")
    lines.append("")

    # 2 Via publica
    raw_esc = raw["escenario_hecho"]
    prep_esc = prep["escenario_hecho"]
    via_labels_raw = [
        "Vía Pública",
        "Vía pública",
        "Calle (Autopista,Avenida,Dentro de La Ciudad)",
        "Calle (autopista, avenida, dentro de la ciudad)",
        "Vía pública o calle",
    ]
    lines += [
        "## 2. Homologacion — via publica / calle",
        "",
        "| Etiqueta en fuente | Casos |",
        "|---------------------|------:|",
    ]
    for lbl in via_labels_raw:
        cnt = int((raw_esc == lbl).sum())
        if cnt:
            lines.append(f"| {lbl} | {cnt:,} |")
    canon = int((prep_esc == "Vía pública o calle").sum())
    lines += [
        "",
        f"**Tras preparacion:** categoria unificada «Vía pública o calle» = **{canon:,}** casos "
        f"({canon / N * 100:.1f} % del total).",
        "",
    ]

    # 3 Faltantes pertenencia_etnica
    def miss_pct_raw(s: pd.Series) -> float:
        norm = s.map(_norm_text)
        m = s.isna() | norm.isin(MISSING_PATTERNS)
        return float(m.mean() * 100)

    def miss_pct_prep(s: pd.Series) -> float:
        return float((s.isna() | s.astype(str).str.strip().eq("Sin informacion")).mean() * 100)

    lines += [
        "## 3. Faltantes — pertenencia_etnica (ejemplo)",
        "",
        "| Momento | % «Sin informacion» |",
        "|---------|--------------------:|",
        f"| CSV crudo (antes de estandarizar en prepare) | {miss_pct_raw(raw['pertenencia_etnica']):.2f} % |",
        f"| Dataset preparado | {miss_pct_prep(prep['pertenencia_etnica']):.2f} % |",
        "",
        "Nota: «Sin pertenencia étnica» **no** es faltante; es categoria valida INMLCF.",
        "",
    ]

    # 4 Severidad
    old_sev = raw["dias_incapacidad"].map(_old_severidad_from_digits).value_counts()
    new_sev = prep["severidad_categoria"].value_counts()
    lines += [
        "## 4. Severidad medicolegal — antes vs despues de correccion",
        "",
        "**Antes (heuristica incorrecta: primer digito del texto):**",
        "",
        "| Categoria erronea | Casos | % |",
        "|-------------------|------:|--:|",
    ]
    for cat, n in old_sev.items():
        lines.append(f"| {cat} | {int(n):,} | {n / N * 100:.1f} % |")
    lines += [
        "",
        "**Despues (mapeo explicito intervalos INMLCF):**",
        "",
        "| Categoria INMLCF | Casos | % |",
        "|------------------|------:|--:|",
    ]
    for cat, n in new_sev.items():
        lines.append(f"| {cat} | {int(n):,} | {n / N * 100:.1f} % |")
    lines.append("")

    # 5 sexo agresor
    lines += [
        "## 5. Homologacion — sexo_agresor",
        "",
        "| Etiqueta fuente | Casos |",
        "|-----------------|------:|",
    ]
    for lbl in ["Transgénero", "Transgenero"]:
        lines.append(f"| {lbl} | {int((raw['sexo_agresor'] == lbl).sum()):,} |")
    lines += [
        "",
        f"Tras preparacion «Transgénero»: **{int((prep['sexo_agresor'] == 'Transgénero').sum()):,}** casos.",
        "",
        "## Uso en sustentacion",
        "",
        "- Mostrar esta pagina o exportar tablas a Excel desde `dataset_limpio.csv`.",
        "- Ejecutar `python analysis/verificar_preparacion.py` para verificacion casefold reproducible.",
        "",
    ]

    path = OUT_DIR / "comparacion_antes_despues.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidencia: {path}")


if __name__ == "__main__":
    main()
