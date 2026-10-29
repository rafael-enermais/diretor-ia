# -*- coding: utf-8 -*-
"""Diretor.IA - Categorias: os indicadores de uma categoria, com valor/meta/status, e o detalhe e o historico de cada um."""
import pandas as pd
import streamlit as st

import base
import detalhe_ui
import graficos
import catalogo
import metricas_dados as md
import painel
import reports

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
    try:
        hist = md.ler_historico(banco, item_id)                 # so' deste item (alimenta os avisos de variacao e o historico abaixo)
    except Exception as exc:                                    # noqa: BLE001
        base.falha(banco, "categorias", "ler_historico", exc, usuario)
        hist = []
    st.markdown("**Detalhe do número (o que está por trás do valor)**")
    for l in atuais_item:
        nome = " · ".join(x for x in (l.get("empresa"), l.get("obra"), l.get("un")) if x) or "geral"
        with st.expander(f'{nome} — {md.periodo_br(l.get("periodo"))}', expanded=len(atuais_item) == 1):
            detalhe_ui.mostrar(l, hist)
    try:                                                        # pendencias em aberto que o Diretor vinculou a este indicador (nao trava a tela se falhar)
        ligadas = [i for i in reports.listar(banco) if i.get("vinculo_item_id") == item_id and i["situacao"] in reports.ABERTAS] if reports.instalado(banco) else []
    except Exception:                                           # noqa: BLE001
        ligadas = []
    if ligadas:
        st.markdown("**Pendências em aberto ligadas a este indicador**")
        ROT = {"critica": "🔴 Crítica", "alta": "🟠 Alta", "media": "🟡 Média", "baixa": "⚪ Baixa"}
        st.dataframe(pd.DataFrame([{"Nº": i["id"], "Colaborador": i["colaborador"], "Urgência": ROT[i["urgencia"]], "Título": i.get("titulo") or "", "Semana": i["semana_de"]} for i in ligadas]),
                     hide_index=True, width="stretch", column_config={"Semana": st.column_config.DateColumn("Semana", format="DD/MM/YYYY")})
        st.caption("Para ver ou editar, abra **Reports e pendências**.")
    if st.toggle("Mostrar histórico mês a mês", key="cat_hist"):
        if hist:
            serie = {}
            for h in hist:
                if not (h.get("empresa") or h.get("obra") or h.get("un")) and h.get("realizado") is not None:
                    serie[h["periodo"]] = float(h["realizado"])
            if len(serie) >= 2:
                graficos.mostrar_linhas(pd.Series(serie, name="Realizado").sort_index(), altura=220)
                st.caption("Evolução do valor realizado (só indicadores sem divisão por empresa/obra/UN).")
            st.dataframe(pd.DataFrame(painel.linhas_detalhe([{**h, "detalhe": None} for h in hist])).drop(columns=["Atualizado"]), hide_index=True, width="stretch")
        else:
            st.caption("Sem histórico.")
base.botao_atualizar()
