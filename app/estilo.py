# -*- coding: utf-8 -*-
"""Diretor.IA - estilo (cores da marca: azul #171C60 e laranja #F99D20). So CSS; nenhum dado passa por aqui."""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
[data-testid="stMainBlockContainer"]{ max-width: 100% !important; padding-left: clamp(1rem, 3vw, 3rem) !important; padding-right: clamp(1rem, 3vw, 3rem) !important; }
[data-testid="stMetric"]{ background:#F3F5F9; border-radius:10px; padding:.7rem .9rem; border-left:4px solid #F99D20; }
[data-testid="stMetricLabel"]{ color:#171C60; }
h1, h2, h3{ color:#171C60; }
[data-testid="stSidebarContent"]{ display:flex; flex-direction:column; }
.dir-rodape{ margin-top:2rem; padding-top:.6rem; border-top:1px solid rgba(23,28,96,.18); font-size:.7rem; color:rgba(23,28,96,.65); line-height:1.4; }
@media (max-width: 640px){ [data-testid="stMetric"]{ padding:.5rem .6rem; } }
</style>
"""


def aplicar() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
