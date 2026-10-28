# -*- coding: utf-8 -*-
"""Diretor.IA - Entregaveis: os 44 entregaveis da matriz, com responsavel (so o 1o nome), prazo, meta e resultado quando houver."""
import pandas as pd
import streamlit as st

import base
import painel

banco, usuario, papel = base.contexto()
st.title("Entregáveis")
itens, atuais, por_item = base.carregar_painel(banco, "entregaveis", usuario)

linhas = painel.tabela_entregas(itens, por_item)
if not linhas:
    st.warning("O catálogo de entregáveis ainda não foi carregado no banco.")
    st.stop()

df = pd.DataFrame(linhas)
c1, c2, c3 = st.columns(3)
resp = c1.multiselect("Responsável", sorted(df["Responsável"].unique()))
prazo = c2.multiselect("Prazo", sorted(df["Prazo"].unique()))
apur = c3.multiselect("Apuração", sorted(df["Apuração"].unique()))
if resp:
    df = df[df["Responsável"].isin(resp)]
if prazo:
    df = df[df["Prazo"].isin(prazo)]
if apur:
    df = df[df["Apuração"].isin(apur)]
st.caption(f"{len(df)} de {len(linhas)} entregáveis")
st.dataframe(df, hide_index=True, width="stretch")
st.caption("«Apuração»: Checklist = alguém confirma que fez; Medido nos dados = o app mede sozinho; Misto = os dois. Sem resultado gravado, aparece «Sem lançamento».")
base.botao_atualizar()
