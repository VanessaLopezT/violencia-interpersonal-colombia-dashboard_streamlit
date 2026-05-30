# -*- coding: utf-8 -*-
"""Tarjetas KPI con texto completo (sin truncar)."""

from __future__ import annotations

import html

import streamlit as st

from app.theme import COLOR_PRIMARY, FONT_FAMILY


def _value_font_size(value: str) -> str:
    n = len(value.replace("\n", " "))
    if n > 42:
        return "0.88rem"
    if n > 24:
        return "1rem"
    return "1.15rem"


def _kpi_html(label: str, value: str, *, spaced: bool = False) -> str:
    safe_label = html.escape(label)
    safe_value = html.escape(value).replace("\n", "<br>")
    font_size = _value_font_size(value)
    margin_top = "0.65rem" if spaced else "0"
    return f"""
<div style="
    margin-top:{margin_top};
    background:#e8f1f8;
    border:1px solid #9bbfd4;
    border-left:4px solid {COLOR_PRIMARY};
    border-radius:0.5rem;
    min-height:5.75rem;
    box-sizing:border-box;
    box-shadow:0 2px 6px rgba(30, 58, 95, 0.12);
    overflow:hidden;
    font-family:{FONT_FAMILY};
    width:100%;
">
  <div style="
      font-size:0.82rem;
      font-weight:700;
      color:{COLOR_PRIMARY};
      background:#d4e4f2;
      margin:0;
      padding:0.55rem 1rem 0.45rem 1rem;
      line-height:1.35;
      border-bottom:1px solid #b8c9d9;
  ">{safe_label}</div>
  <div style="
      font-size:{font_size};
      font-weight:600;
      color:#1e1e1e;
      line-height:1.45;
      padding:0.7rem 1rem 0.9rem 1rem;
      background:#e8f1f8;
      word-wrap:break-word;
      overflow-wrap:anywhere;
      white-space:normal;
  ">{safe_value}</div>
</div>
"""


def _emit_html(fragment: str, *, container=None) -> None:
    target = container if container is not None else st
    if hasattr(target, "html"):
        target.html(fragment)
    else:
        target.markdown(fragment, unsafe_allow_html=True)


def render_kpi_card(col, label: str, value: str) -> None:
    with col:
        _emit_html(_kpi_html(label, value))


def render_kpi_block(label: str, value: str, *, spaced: bool = False, container=None) -> None:
    """Tarjeta KPI a ancho completo (inicio, sidebar)."""
    _emit_html(_kpi_html(label, value, spaced=spaced), container=container)


def render_kpi_row(kpis: list[tuple[str, str]]) -> None:
    cols = st.columns(len(kpis), gap="medium")
    for col, (label, value) in zip(cols, kpis):
        render_kpi_card(col, label, value)
