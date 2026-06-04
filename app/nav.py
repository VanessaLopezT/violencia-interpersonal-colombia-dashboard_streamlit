# -*- coding: utf-8 -*-
"""Botones de navegacion entre paginas."""

from __future__ import annotations

import streamlit as st

from app.theme import COLOR_PRIMARY, FONT_FAMILY

SECTIONS: list[dict[str, str]] = [
    {
        "id": "inicio",
        "titulo": "Inicio",
        "desc": "Resumen",
        "path": "streamlit_app.py",
    },
    {
        "id": "panorama",
        "titulo": "Panorama",
        "desc": "Por año",
        "path": "pages/1_Panorama.py",
    },
    {
        "id": "territorio",
        "titulo": "Territorio",
        "desc": "Departamentos",
        "path": "pages/2_Territorio.py",
    },
    {
        "id": "personas",
        "titulo": "Personas",
        "desc": "Perfil y hora",
        "path": "pages/3_Personas_y_tiempo.py",
    },
    {
        "id": "patrones",
        "titulo": "Patrones",
        "desc": "Lesión",
        "path": "pages/4_Patrones_y_cierre.py",
    },
    {
        "id": "modelo",
        "titulo": "Modelo",
        "desc": "Predictivo",
        "path": "pages/5_Modelo_predictivo.py",
    },
]

_NAV_CSS = f"""
<style>
/* Barra superior: fila de 6 botones de seccion */
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child) {{
    align-items: stretch;
    gap: 0.65rem;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
> div[data-testid="column"] {{
    flex: 1 1 0%;
    min-width: 0;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] {{
    width: 100%;
    margin: 0;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] > button {{
    height: 5.75rem;
    min-height: 5.75rem;
    max-height: 5.75rem;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.55rem 0.5rem;
    white-space: pre-line;
    line-height: 1.35;
    font-weight: 600;
    font-size: 0.88rem;
    font-family: {FONT_FAMILY};
    border-radius: 0.5rem;
    box-sizing: border-box;
    text-align: center;
    overflow: hidden;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_PRIMARY};
    color: #ffffff;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background-color: #2a4f7a;
    border-color: #2a4f7a;
    color: #ffffff;
}}
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] > button[kind="secondary"],
div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6):last-child)
div[data-testid="stButton"] > button:disabled {{
    background-color: #d8e2ec;
    border: 1px solid {COLOR_PRIMARY};
    color: {COLOR_PRIMARY};
    opacity: 1;
    cursor: default;
}}
/* Botones inferiores (siguiente / volver) */
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[kind="secondary"] {{
    min-height: 3rem;
    white-space: pre-line;
    line-height: 1.35;
    font-weight: 600;
    font-family: {FONT_FAMILY};
    border-radius: 0.5rem;
    box-sizing: border-box;
}}
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
    color: #ffffff;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background-color: #2a4f7a;
    border-color: #2a4f7a;
    color: #ffffff;
}}
div[data-testid="stButton"] > button[kind="secondary"] {{
    background-color: #e8f1f8;
    border: 1px solid {COLOR_PRIMARY};
    color: {COLOR_PRIMARY};
}}
</style>
"""


def inject_nav_styles() -> None:
    if st.session_state.get("_nav_styles"):
        return
    st.markdown(_NAV_CSS, unsafe_allow_html=True)
    st.session_state["_nav_styles"] = True


def _section_label(section: dict[str, str]) -> str:
    if section["id"] == "inicio":
        return f"{section['titulo']}\n{section['desc']}"
    idx = SECTIONS.index(section)
    return f"{idx} · {section['titulo']}\n{section['desc']}"


def render_section_nav(current: str) -> None:
    """Barra de navegacion superior (5 vistas). `current`: id de la seccion activa."""
    inject_nav_styles()
    cols = st.columns(len(SECTIONS), gap="small")
    for col, section in zip(cols, SECTIONS):
        with col:
            label = _section_label(section)
            key = f"nav_{current}_{section['id']}"
            if section["id"] == current:
                st.button(
                    label,
                    use_container_width=True,
                    type="secondary",
                    key=key,
                    disabled=True,
                )
            elif st.button(label, use_container_width=True, type="primary", key=key):
                st.switch_page(section["path"])


def render_sidebar_section_nav(current_id: str) -> None:
    """Anterior / Siguiente en el panel lateral."""
    inject_nav_styles()
    idx = next(i for i, s in enumerate(SECTIONS) if s["id"] == current_id)
    prev_sec = SECTIONS[idx - 1] if idx > 0 else None
    next_sec = SECTIONS[idx + 1] if idx < len(SECTIONS) - 1 else None

    c1, c2 = st.sidebar.columns(2)
    with c1:
        if prev_sec and st.button(
            "Anterior",
            use_container_width=True,
            type="secondary",
            key=f"sidebar_prev_{current_id}",
        ):
            st.switch_page(prev_sec["path"])
        elif not prev_sec:
            st.button(
                "Anterior",
                use_container_width=True,
                type="secondary",
                key=f"sidebar_prev_{current_id}_off",
                disabled=True,
            )
    with c2:
        if next_sec and st.button(
            "Siguiente",
            use_container_width=True,
            type="primary",
            key=f"sidebar_next_{current_id}",
        ):
            st.switch_page(next_sec["path"])
        elif not next_sec:
            st.button(
                "Siguiente",
                use_container_width=True,
                type="primary",
                key=f"sidebar_next_{current_id}_off",
                disabled=True,
            )


def nav_button(label: str, page: str, *, key: str, primary: bool = True) -> None:
    """Boton de navegacion inferior (siguiente / volver)."""
    inject_nav_styles()
    kind = "primary" if primary else "secondary"
    if st.button(label, use_container_width=True, type=kind, key=key):
        st.switch_page(page)
