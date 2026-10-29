# -*- coding: utf-8 -*-
"""Diretor.IA - desenho (Streamlit) do DETALHE de um indicador: composicao, avisos de numero fora do comum, campos, tabelas com grafico. Calculo em detalhe.py."""
import pandas as pd
import streamlit as st

import detalhe as D
import graficos


def _t(txt) -> str:
    return str(txt).replace("$", "\\$")          # o Streamlit trata $...$ como formula


def mostrar(linha: dict, historico: list | None = None) -> None:
    interp = D.interpretar(linha.get("detalhe"))
    comp = D.composicao(linha)
    if comp:
        st.markdown(_t(f"**Composição do número:** {comp}"), help="Numerador ÷ denominador gravados pelo app de origem; o painel só faz a divisão para mostrar o percentual.")
    for a in D.avisos(linha, interp, historico):
        st.warning(_t(a), icon="👀")
    if interp["campos"]:
        st.dataframe(pd.DataFrame(interp["campos"], columns=["Campo", "Valor"]), hide_index=True, width="stretch")
    for t in interp["tabelas"]:
        st.markdown(_t(f"**{t['titulo']}**"))
        st.dataframe(pd.DataFrame(t["linhas"]), hide_index=True, width="stretch")
        pontos = [(b["rotulo"], b["valor"]) for b in t["bruto"] if b.get("rotulo") and b.get("valor") is not None]
        if len(pontos) >= 2:
            graficos.mostrar_barras(pd.DataFrame({"Valor": [v for _, v in pontos]}, index=[r for r, _ in pontos]), altura=200)
    if interp["texto"]:
        st.caption("Como o número foi apurado")
        st.text(interp["texto"][:1500])
    if not (comp or interp["campos"] or interp["tabelas"] or interp["texto"]):
        st.caption("O app de origem não gravou detalhe para este número.")
