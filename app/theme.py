# -*- coding: utf-8 -*-
"""Paleta visual academica compartida por Plotly y Streamlit."""

# Serie principal
COLOR_PRIMARY = "#1E3A5F"  # azul marino

# Categorias semanticas
COLOR_ZONA = {
    "Cabecera Municipal": "#2A9D8F",
    "Centro Poblado Y Rural Disperso": "#C17817",
    "Sin informacion": "#94A3B8",
}

# Graficos multiserie (edad, mecanismos)
PALETTE_CATEGORICAL = [
    "#1E3A5F",
    "#3D7EA6",
    "#2A9D8F",
    "#7B68A6",
    "#C17817",
    "#5B8BA0",
    "#94A3B8",
    "#4A6741",
]

# Un tono claramente distinto por grupo quinquenal (19 categorías)
PALETA_GRUPO_EDAD = [
    "#1E3A5F",
    "#C17817",
    "#2A9D8F",
    "#7B68A6",
    "#D4709B",
    "#3D7EA6",
    "#4A6741",
    "#E07A5F",
    "#5C6BC0",
    "#00897B",
    "#9C6644",
    "#457B9D",
    "#BC4749",
    "#6A994E",
    "#8338EC",
    "#219EBC",
    "#8D6E63",
    "#F4A261",
    "#FFB703",
]

# Heatmap (claro → oscuro)
HEATMAP_SCALE = [
    [0.0, "#E8F1F8"],
    [0.35, "#9BBFD4"],
    [0.7, "#3D7EA6"],
    [1.0, "#1E3A5F"],
]

PLOTLY_TEMPLATE = "plotly_white"
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
PLOTLY_CONFIG = {"displayModeBar": False}
