# -*- coding: utf-8 -*-
"""Diretor.IA - Prontidao e fontes: o que ja esta pronto, o que depende de qual app e o que ainda nao recebeu dado. (Administrador ve tambem a verificacao tecnica.)"""
import pandas as pd
import streamlit as st

import acesso
import base
import diagnostico
import logs_app
import prontidao

banco, usuario, papel = base.contexto()
st.title("Prontidão e fontes")
st.caption("Quanto da matriz de metas já está ligada a uma fonte e já recebendo dado. Cresce conforme cada app é terminado.")
itens, atuais, por_item = base.carregar_painel(banco, "prontidao", usuario)

if not itens:
    st.warning("O catálogo ainda não foi carregado no banco.")
    st.stop()

st.subheader("Por situação")
st.dataframe(pd.DataFrame(prontidao.por_situacao(itens, por_item)), hide_index=True, width="stretch")
st.caption("Existe no app = já calculado em algum app · Parcial = falta ligar/ajustar · Falta construir = ainda não existe · Input manual = alguém digita.")

st.subheader("Por app / sistema de origem")
st.dataframe(pd.DataFrame(prontidao.por_fonte(itens, por_item)), hide_index=True, width="stretch")

with st.expander("Indicadores que ainda não receberam valor"):
    st.dataframe(pd.DataFrame(prontidao.sem_dado_ainda(itens, por_item)), hide_index=True, width="stretch")

if papel == acesso.ADMIN:
    st.subheader("Verificação técnica (administrador)")
    if st.button("Rodar verificação agora"):
        resultados = diagnostico.rodar(banco)
        st.session_state["_dir_diag"] = resultados
        logs_app.registrar(banco, "evento", "prontidao", "verificacao", "Verificação técnica executada", usuario=usuario,
                           contexto={"falhas": sum(1 for r in resultados if not r["ok"])})
    for r in st.session_state.get("_dir_diag", []):
        (st.success if r["ok"] else st.error)(f'**{r["verificacao"]}** — {r["detalhe"]}')
base.botao_atualizar()
