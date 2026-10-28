# -*- coding: utf-8 -*-
"""Diretor.IA - Categorias: os indicadores de uma categoria, com valor/meta/status, e o detalhe e o historico de cada um."""
import pandas as pd
import streamlit as st

import base
import catalogo
import metricas_dados as md
import painel
from texto import limpar_texto

banco, usuario, papel = base.contexto()
st.title("Categorias")
itens, atuais, por_item = base.carregar_painel(banco, "categorias", usuario)

cats = catalogo.categorias_em_ordem(itens)
if not cats:
    st.warning("O catálogo ainda não foi carregado no banco.")
    st.stop()

cat = st.selectbox("Categoria", cats)
linhas = painel.tabela_indicadores(itens, por_item, cat)
st.dataframe(pd.DataFrame(linhas).drop(columns=["Categoria"]), hide_index=True, width="stretch")
st.caption("Valor, meta e status vêm do app de origem (já calculados). Onde aparece «—» e «Sem lançamento», o dado ainda não chegou.")

st.subheader("Detalhe de um indicador")
opcoes = {f'{l["ID"]} · {l["Indicador"]}': l["ID"] for l in linhas}
escolha = st.selectbox("Indicador", list(opcoes), key="cat_ind")
item_id = opcoes[escolha]
item = next(i for i in itens if i["item_id"] == item_id)
c1, c2, c3 = st.columns(3)
c1.markdown(f'**Fonte do dado:** {item.get("fonte") or "—"}')
c2.markdown(f'**Referência:** {item.get("referencia") or "—"}')
c3.markdown(f'**App de origem:** {item.get("app_origem") or "—"}')

atuais_item = por_item.get(item_id, [])
if not atuais_item:
    st.info("Este indicador ainda não tem valor gravado.")
else:
    st.markdown("**Último valor gravado (por empresa/obra/UN, quando houver)**")
    st.dataframe(pd.DataFrame(painel.linhas_detalhe(atuais_item)), hide_index=True, width="stretch")
    for l in atuais_item:
        det = limpar_texto(l.get("detalhe"), 1500)
        if det:
            with st.expander(f'Como o número foi apurado — {l.get("empresa") or "geral"} {l.get("obra") or ""}'.strip()):
                st.text(det)
    if st.toggle("Mostrar histórico mês a mês", key="cat_hist"):
        try:
            hist = md.ler_historico(banco, item_id)
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "categorias", "ler_historico", exc, usuario)
            hist = []
        if hist:
            st.dataframe(pd.DataFrame(painel.linhas_detalhe([{**h, "detalhe": None} for h in hist])).drop(columns=["Atualizado"]), hide_index=True, width="stretch")
        else:
            st.caption("Sem histórico.")
base.botao_atualizar()
