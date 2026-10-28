# -*- coding: utf-8 -*-
"""Diretor.IA - Visao geral: o retrato do momento (quantos indicadores/entregas, quantos ja tem valor, status) e um quadro por categoria."""
import pandas as pd
import streamlit as st

import base
import catalogo
import painel
from fuso import fmt_br
import metricas_dados as md

banco, usuario, papel = base.contexto()
st.title("Visão geral")
itens, atuais, por_item = base.carregar_painel(banco, "visao_geral", usuario)

if not itens:
    st.warning("O catálogo de indicadores e entregas ainda não foi carregado no banco. Quem administra o painel precisa rodar a carga inicial.")
    st.stop()

r = painel.resumo_geral(itens, por_item)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Indicadores", r["indicadores"], help="Os indicadores da matriz de metas da Diretoria Financeira.")
c2.metric("Com valor já gravado", f'{r["ind_com_valor"]} de {r["indicadores"]}', help="Indicadores que já têm pelo menos um valor calculado e gravado pelo app de origem.")
c3.metric("Entregáveis", r["entregas"])
c4.metric("Entregáveis com resultado", f'{r["ent_com_valor"]} de {r["entregas"]}')

st.subheader("Situação dos indicadores")
s = r["status_indicadores"]
k1, k2, k3, k4 = st.columns(4)
k1.metric("🟢 No alvo", s["No alvo"])
k2.metric("🟡 Atenção", s["Atenção"])
k3.metric("🔴 Fora da meta", s["Fora da meta"])
k4.metric("⚪ Sem lançamento", s["Sem lançamento"], help="Ainda não chegou valor deste indicador. Não significa que esteja ruim: significa que falta o dado.")

if r["ind_com_valor"] == 0:
    st.info("Nenhum indicador recebeu valor ainda. Conforme cada app de origem (por exemplo, o GDF) gravar o mês, os números aparecem aqui sozinhos. "
            "Veja em **Prontidão e fontes** o que já está pronto e o que falta.")

st.subheader("Por categoria")
tab = pd.DataFrame(painel.resumo_por_categoria(itens, por_item))
st.dataframe(tab, hide_index=True, width="stretch")

datas = [md.ultima_atualizacao(l) for l in por_item.values()]
datas = [d for d in datas if d]
st.caption(f"Última gravação recebida: {fmt_br(max(datas)) if datas else '—'} · Matriz de metas: {catalogo.versao_matriz(itens)} · "
           "O painel só mostra o que os apps de origem já calcularam; não recalcula nada.")
base.botao_atualizar()
