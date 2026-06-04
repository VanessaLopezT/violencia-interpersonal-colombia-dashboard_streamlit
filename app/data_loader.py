# -*- coding: utf-8 -*-
"""Carga de agregados precomputados para el dashboard."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED = PROJECT_ROOT / "data" / "processed"

AGG_FILES = {
    "territorial": "agg_territorial.parquet",
    "demografia": "agg_demografia.parquet",
    "patrones": "agg_patrones.parquet",
    "dia_hora": "agg_dia_hora.parquet",
    "filtros": "agg_filtros.parquet",
}


@dataclass(frozen=True)
class Aggregates:
    territorial: pd.DataFrame
    demografia: pd.DataFrame
    patrones: pd.DataFrame
    dia_hora: pd.DataFrame
    filtros: pd.DataFrame
    total_nacional: int


REQUIRED_FILTER_COLS = [
    "municipio_hecho",
    "pertenencia_etnica",
    "pertenencia_grupal",
    "ciclo_vital",
]


def _require_aggs() -> None:
    missing = [
        name for name, fname in AGG_FILES.items() if not (PROCESSED / fname).exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"Faltan agregados: {missing}. Ejecute: python analysis/run.py"
        )
    filtros = pd.read_parquet(PROCESSED / AGG_FILES["filtros"])
    faltan = [c for c in REQUIRED_FILTER_COLS if c not in filtros.columns]
    if faltan:
        raise FileNotFoundError(
            f"Agregados desactualizados (faltan {faltan}). Ejecute: python analysis/run.py"
        )


@st.cache_resource
def load_aggregates() -> Aggregates:
    _require_aggs()
    data = {k: pd.read_parquet(PROCESSED / v) for k, v in AGG_FILES.items()}
    total = int(data["filtros"]["casos"].sum())
    return Aggregates(total_nacional=total, **data)
