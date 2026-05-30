"""Carga, limpieza y preparacion del dataset."""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATASET_PARQUET = PROJECT_ROOT / "data" / "processed" / "dataset.parquet"
RAW_CSV_GLOB = "Violencia_interpersonal*.csv"
YEAR_MIN, YEAR_MAX = 2015, 2024

COLUMN_RENAME_MAP = {
    "ID": "id",
    "Año del hecho": "anio_hecho",
    "Sexo de la victima": "sexo_victima",
    "Grupo de Edad Quinquenal": "grupo_edad_quinquenal",
    "Grupo Mayor Menor de Edad": "grupo_mayor_menor_edad",
    "Grupo de Edad judicial": "grupo_edad_judicial",
    "Ciclo Vital": "ciclo_vital",
    "País de Nacimiento": "pais_nacimiento",
    "Escolaridad": "escolaridad",
    "Estado Civil": "estado_civil",
    "Tipo de Discapacidad": "tipo_discapacidad",
    "Pertenencia Étnica": "pertenencia_etnica",
    "Orientación Sexual": "orientacion_sexual",
    "Identidad de Género": "identidad_genero",
    "Transgénero": "transgenero",
    "Pertenencia Grupal": "pertenencia_grupal",
    "Mes del hecho": "mes_hecho",
    "Dia del hecho": "dia_hecho",
    "Rango de Hora del Hecho X 3 Horas": "rango_hora",
    "Código Dane Municipio": "codigo_dane_municipio",
    "Municipio del hecho DANE": "municipio_hecho",
    "Departamento del hecho DANE": "departamento_hecho",
    "Código Dane Departamento": "codigo_dane_departamento",
    "Localidad del Hecho": "localidad_hecho",
    "Zona del Hecho": "zona_hecho",
    "Escenario del Hecho": "escenario_hecho",
    "Actividad Durante el Hecho": "actividad_hecho",
    "Circunstancia del Hecho Detallada": "circunstancia_detallada",
    "Contexto del Hecho": "contexto_hecho",
    "Mecanismo Causal de la Lesión no Fatal": "mecanismo_causal",
    "Diagnostico Topográfico de la Lesión no Fatal": "diagnostico_topografico",
    "Sexo del Agresor": "sexo_agresor",
    "Presunto Agresor Detallado": "presunto_agresor",
    "Días de Incapacidad Medicolegal": "dias_incapacidad",
    "Pueblo Indígena": "pueblo_indigena",
}

MISSING_PATTERNS = [
    "sin informacion", "sin información", "no reportado", "no aplica",
    "desconocido", "no definido", "no especificado", "ignorado", "999",
]

INCAPACIDAD_MAP = {
    "0": 0, "1 a 5": 3, "6 a 15": 10, "16 a 30": 23, "31 a 60": 45,
    "61 a 90": 75, "91 a 120": 105, "121 a 150": 135,
    "151 o mas": 180, "151 o más": 180,
}


def _parse_incapacidad(value: object) -> float | np.nan:
    if pd.isna(value):
        return np.nan
    text = _norm_text(value)
    if text in INCAPACIDAD_MAP:
        return float(INCAPACIDAD_MAP[text])
    digits = re.findall(r"\d+", str(text))
    if digits:
        return float(digits[0])
    return np.nan


def _norm_text(value: object) -> object:
    if pd.isna(value):
        return np.nan
    text = unicodedata.normalize("NFKD", str(value).strip())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).lower()


def _find_csv() -> Path:
    matches = sorted(DATA_RAW.glob(RAW_CSV_GLOB))
    if not matches:
        raise FileNotFoundError(f"No se encontro CSV en {DATA_RAW}")
    return matches[0]


def _read_csv(path: Path) -> pd.DataFrame:
    """Lee el CSV probando codificaciones; el texto se normaliza a UTF-8 despues."""
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise UnicodeDecodeError(
        "csv", b"", 0, 0, f"No se pudo leer {path}: {last_error}"
    )


ORDERED_COLUMNS = list(COLUMN_RENAME_MAP.values())


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    if len(df.columns) != len(ORDERED_COLUMNS):
        raise ValueError(
            f"Se esperaban {len(ORDERED_COLUMNS)} columnas, se encontraron {len(df.columns)}"
        )
    out = df.copy()
    out.columns = ORDERED_COLUMNS
    return out


def prepare() -> pd.DataFrame:
    """Carga el CSV, limpia, crea variables derivadas y devuelve el dataframe listo."""
    from app.text_es import apply_to_dataframe, canonize_column, normalizar_franja, normalize_text

    df = _read_csv(_find_csv())
    df = _rename_columns(df)

    # Normalizar UTF-8 en todas las columnas de texto antes de cualquier agregacion
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(lambda v: normalize_text(v) if pd.notna(v) else v)

    for col in df.select_dtypes(include=["object", "string"]).columns:
        norm = df[col].map(_norm_text)
        df.loc[norm.isin(MISSING_PATTERNS), col] = "Sin informacion"

    if "rango_hora" in df.columns:
        df["rango_hora"] = df["rango_hora"].map(
            lambda v: normalizar_franja(v) if pd.notna(v) else v
        )

    for col in [
        "departamento_hecho", "municipio_hecho", "escenario_hecho",
        "presunto_agresor", "mecanismo_causal", "zona_hecho",
    ]:
        if col in df.columns:
            df[col] = canonize_column(df[col])

    df["anio_hecho"] = pd.to_numeric(df["anio_hecho"], errors="coerce").astype("Int64")
    df["dias_incapacidad_num"] = df["dias_incapacidad"].map(_parse_incapacidad)
    df = df[(df["anio_hecho"] >= YEAR_MIN) & (df["anio_hecho"] <= YEAR_MAX)].reset_index(drop=True)

    df["anio_mes"] = df["anio_hecho"].astype(str) + "-" + df["mes_hecho"].astype(str)
    df["fin_semana"] = df["dia_hecho"].isin(
        ["Sabado", "Sábado", "Domingo", "6 Sabado", "7 Domingo"]
    )

    def severidad(dias: float) -> str:
        if pd.isna(dias):
            return "Sin informacion"
        if dias == 0:
            return "Sin incapacidad"
        if dias <= 5:
            return "Leve (1-5 dias)"
        if dias <= 15:
            return "Moderada (6-15 dias)"
        if dias <= 30:
            return "Alta (16-30 dias)"
        return "Muy alta (>30 dias)"

    df["severidad_categoria"] = df["dias_incapacidad_num"].map(severidad)

    df = apply_to_dataframe(df)

    # contexto_hecho es constante en el 100 % de filas; no aporta al análisis.
    if "contexto_hecho" in df.columns:
        df = df.drop(columns=["contexto_hecho"])

    return df


def save_dataset(df: pd.DataFrame) -> Path:
    DATASET_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DATASET_PARQUET, index=False)
    return DATASET_PARQUET
