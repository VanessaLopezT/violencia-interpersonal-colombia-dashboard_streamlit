# -*- coding: utf-8 -*-
"""Normalizacion Unicode y equivalencias de dominio INMLCF."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Equivalencias semanticas documentadas (taxonomia INMLCF / homologacion DANE).
# No corrigen encoding: el CSV se lee en UTF-8 en src/prepare._read_csv.
DEPTO_BOGOTA = "Bogotá D.C."

DOMAIN_ALIASES: dict[str, str] = {
    "Bogotá, D.C.": "Bogotá D.C.",
    # Escenario: variantes INMLCF de vía pública / calle.
    "Calle (Autopista,Avenida,Dentro de La Ciudad)": "Vía pública o calle",
    "Calle (autopista, avenida, dentro de la ciudad)": "Vía pública o calle",
    "Vía Pública": "Vía pública o calle",
    "Vía pública": "Vía pública o calle",
    # Escenario: misma categoría con distinto formato de mayúsculas y puntuación.
    "Establecimientos dedicados a la administración pública (cortes, juzgados, ministerios, etc.)": (
        "Establecimientos Dedicados a la Administración Pública (Cortes,Juzgados,Ministerios,Etc)"
    ),
    # Presunto agresor: unificar formato Amigo(a) / Amigo (a).
    "Amigo (a)": "Amigo(a)",
    # Sexo agresor: variante sin tilde (39) → forma modal con tilde (45).
    "Transgenero": "Transgénero",
}

CANON_COLS = [
    "departamento_hecho",
    "municipio_hecho",
    "escenario_hecho",
    "presunto_agresor",
    "mecanismo_causal",
    "zona_hecho",
    "circunstancia_detallada",
    "mes_hecho",
    "dia_hecho",
    "pertenencia_etnica",
    "escolaridad",
    "estado_civil",
    "actividad_hecho",
    "sexo_agresor",
]

UI = {
    "app_title": "Violencia interpersonal registrada en Colombia",
    "periodo": "Años",
    "territorio": "Departamento",
    "municipio": "Municipio / ciudad",
    "zona": "Zona del hecho",
    "sexo_victima": "Sexo de la víctima",
    "pertenencia_etnica": "Pertenencia étnica",
    "ciclo_vital": "Ciclo vital",
    "todos": "Todos los departamentos",
    "todos_municipio": "Todos los municipios",
    "todos_zona": "Todas las zonas",
    "todos_sexo": "Ambos sexos",
    "todos_etnia": "Toda pertenencia étnica",
    "todos_ciclo": "Todos los ciclos vitales",
    "filtros_territorio": "Territorio",
    "filtros_victima": "Perfil de la víctima",
    "municipio_hint": "Elija un departamento para ver todos sus municipios.",
    "reset": "Restablecer filtros",
    "casos_filtro": "Casos en la selección",
    "pct_total": "Participación del total",
    "inicio_resumen_titulo": "Perfil integrado de su selección",
    "inicio_resumen_caption": (
        "Síntesis de la subpoblación que cumple todos los filtros del panel lateral: "
        "territorio, perfil de víctima y patrones del hecho."
    ),
    "volver_inicio": "Volver al inicio",
    "disclaimer": (
        "Estos datos corresponden a casos registrados en valoración medicolegal, "
        "no a la totalidad de la violencia ocurrida. Interpretar con cautela."
    ),
    "source_url": "https://www.datos.gov.co/en/Justicia-y-Derecho/Violencia-interpersonal-Colombia-a-os-2015-a-2024-/e3xi-4zq5/about_data",
    "source_title": "Violencia interpersonal. Colombia, años 2015 a 2024. Cifras definitivas",
}

STORY = {
    "panorama": {
        "etapa": 1,
        "titulo_menu": "1 · Panorama",
        "pregunta": "Casos registrados por año",
        "siguiente_titulo": "2 · Territorio",
        "siguiente_path": "pages/2_Territorio.py",
    },
    "territorio": {
        "etapa": 2,
        "titulo_menu": "2 · Territorio",
        "pregunta": "Casos por departamento y municipio",
        "siguiente_titulo": "3 · Personas y tiempo",
        "siguiente_path": "pages/3_Personas_y_tiempo.py",
    },
    "personas": {
        "etapa": 3,
        "titulo_menu": "3 · Personas y tiempo",
        "pregunta": "Perfil de víctimas y momento del hecho",
        "siguiente_titulo": "4 · Patrones",
        "siguiente_path": "pages/4_Patrones_y_cierre.py",
    },
    "patrones": {
        "etapa": 4,
        "titulo_menu": "4 · Patrones",
        "pregunta": "Mecanismo, escenario, gravedad y agresor",
        "siguiente_titulo": None,
        "siguiente_path": None,
    },
}

# Valores de sexo_victima en la fuente INMLCF.
SEXO_OPCIONES = ["Ambos", "Hombre", "Mujer"]

CHART_AYUDA: dict[str, str] = {
    "resumen_perfil": (
        "Participación relativa de la modalidad más frecuente en cada dimensión analítica "
        "bajo los filtros activos. Complementa la tabla con una lectura visual rápida."
    ),
    "linea_anual": (
        "Casos registrados por año según los filtros activos. "
        "Un punto más alto indica más registros en ese año."
    ),
    "linea_anual_pct": (
        "Porcentaje de cada año sobre el total nacional (2015–2024). "
        "Sirve para ver si la selección gana o pierde peso relativo."
    ),
    "dept_top10": (
        "Departamentos con más casos en la selección. "
        "La barra más larga concentra más registros; el % es sobre el filtro activo."
    ),
    "zona": (
        "Proporción de casos por zona del hecho. "
        "Compare cabecera municipal frente a centro poblado y rural disperso."
    ),
    "municipios": (
        "Cinco municipios con más registros en el departamento elegido. "
        "No modifica periodo ni departamento del panel lateral."
    ),
    "localidades": (
        "Cinco localidades con más registros en Bogotá D.C. "
        "La ciudad no tiene desglose municipal; se usa localidad del hecho."
    ),
    "edad_sexo": (
        "Distribución por sexo y grupo etario. "
        "Cada barra apilada suma 100 % dentro de hombres o mujeres."
    ),
    "ciclo_ambos": (
        "Participación de cada etapa del ciclo vital sobre el total filtrado. "
        "Cada barra muestra la composición por sexo (azul hombres, lila mujeres)."
    ),
    "ciclo_sexo": (
        "Participación del ciclo vital solo entre víctimas {sexo}. "
        "Las barras suman 100 % dentro de ese sexo."
    ),
    "heatmap_dh": (
        "Registros por día de la semana (filas) y franja horaria (columnas). "
        "Colores más oscuros indican más casos."
    ),
    "top_franjas": (
        "Las cinco combinaciones de día y hora con más registros en la selección."
    ),
    "mecanismos": (
        "Mecanismos de lesión más frecuentes. "
        "La longitud de la barra y el % indican su peso en el filtro activo."
    ),
    "escenarios": (
        "Lugares donde ocurrieron los hechos con mayor frecuencia según el INMLCF."
    ),
    "severidad": (
        "Clasificación medicolegal por días de incapacidad registrados. "
        "No agota la gravedad subjetiva del evento."
    ),
    "agresores": (
        "Tipo de presunto agresor más frecuente en los registros de valoración."
    ),
    "mapa_temporal": (
        "Mapa interactivo de calor que muestra la cantidad de casos de violencia "
        "registrados en cada departamento de Colombia. Presione el botón de reproducción (▶) "
        "en la esquina inferior izquierda para ver la evolución a lo largo del tiempo."
    ),
}


def chart_ayuda(chart_id: str, **kwargs: str) -> str:
    template = CHART_AYUDA[chart_id]
    return template.format(**kwargs) if kwargs else template


def normalize_text(text: object) -> str:
    """Strip, Unicode NFC y alias de dominio (sin parches de encoding)."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text).strip()
    s = unicodedata.normalize("NFC", s)
    return DOMAIN_ALIASES.get(s, s)


def normalizar_franja(text: object) -> str:
    """Unifica espacios en rangos horarios (p. ej. '18:00 a  20:59' -> '18:00 a 20:59')."""
    s = normalize_text(text)
    if not s:
        return s
    return re.sub(r"\s+", " ", s)


def canonize_column(series: pd.Series) -> pd.Series:
    """Unifica variantes ortograficas conservando la modalidad mas frecuente."""
    normalized = series.map(lambda v: normalize_text(v) if pd.notna(v) else v)
    freq = normalized.value_counts()
    canon: dict[str, str] = {}
    for val in normalized.unique():
        if pd.isna(val):
            continue
        key = str(val).casefold()
        if key not in canon or freq.get(val, 0) > freq.get(canon[key], 0):
            canon[key] = val
    return normalized.map(
        lambda v: canon.get(str(v).casefold(), v) if pd.notna(v) else v
    )


def apply_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].map(lambda v: normalize_text(v) if pd.notna(v) else v)
    for col in CANON_COLS:
        if col in out.columns:
            out[col] = canonize_column(out[col])
    return out
