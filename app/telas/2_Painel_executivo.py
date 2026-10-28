# -*- coding: utf-8 -*-
"""Diretor.IA - Painel executivo: o retrato do momento em graficos, pontos de atencao, evolucao com tendencia simples e comparacao lado a lado.
Atualiza sozinho a cada 60 s (leitura do que os apps de origem ja gravaram; nada e' recalculado aqui)."""
import pandas as pd
import streamlit as st

import base
import metricas_dados as md
import painel
import previsao
from formatacao import valor_com_unidade
from fuso import agora_br, fmt_br

banco, usuario, papel = base.contexto()
st.title("Painel executivo")

CORES = ["#2E9E5B", "#F2B134", "#D64545", "#4A7BD0", "#C9CCD8"]


@st.fragment(run_every=60)
def corpo():
    itens, atuais, por_item = base.carregar_painel(banco, "painel_executivo", usuario)
    hist = base.carregar_historico(banco, "painel_executivo", usuario)
    if not itens:
        st.warning("O catálogo ainda não foi carregado no banco.")
        return
    r = painel.resumo_geral(itens, por_item)
    s = r["status_indicadores"]
    datas = [d for d in (md.ultima_atualizacao(l) for l in por_item.values()) if d]
    st.caption(f"Atualiza sozinho a cada 1 minuto · consultado às {agora_br():%H:%M:%S} · última gravação dos apps de origem: {fmt_br(max(datas)) if datas else '—'}")

    c = st.columns(5)
    c[0].metric("Com valor", f'{r["ind_com_valor"]} de {r["indicadores"]}')
    c[1].metric("🟢 No alvo", s["No alvo"])
    c[2].metric("🟡 Atenção", s["Atenção"])
    c[3].metric("🔴 Fora da meta", s["Fora da meta"])
    c[4].metric("🔵 Só informativo", s["Sem meta"])

    st.subheader("Pontos de atenção")
    pa = painel.pontos_de_atencao(itens, por_item)
    if pa:
        st.dataframe(pd.DataFrame(pa)[["ID", "Indicador", "Categoria", "Responsável", "Período", "Valor", "Meta", "% da meta", "Status"]], hide_index=True, width="stretch")
    else:
        st.success("Nenhum indicador em Atenção ou Fora da meta entre os que já têm meta.")

    st.subheader("Situação por categoria")
    cats = pd.DataFrame(painel.resumo_por_categoria(itens, por_item)).set_index("Categoria")
    colunas = ["🟢 No alvo", "🟡 Atenção", "🔴 Fora da meta", "🔵 Sem meta (informativo)", "⚪ Sem lançamento"]
    st.bar_chart(cats[colunas], stack=True, horizontal=True, color=CORES, height=330)
    st.caption("Quanto mais azul/cinza, mais falta chegar meta ou valor dos apps de origem. O painel cresce conforme cada app é terminado.")

    st.subheader("Evolução e tendência")
    com_serie = painel.itens_com_serie(itens, hist)
    if not com_serie:
        st.info("Ainda não há histórico mensal gravado. Quando os apps de origem gravarem mais de um mês, a evolução aparece aqui.")
        return
    rot = {f'{x["id"]} · {x["nome"]} ({x["meses"]} mês(es))': x for x in com_serie}
    x = rot[st.selectbox("Indicador", list(rot), key="pe_ind")]
    serie = md.serie_geral(hist, x["id"])
    tend = previsao.tendencia(serie)
    df = pd.DataFrame({"Realizado": dict(serie)})
    if tend["ok"]:
        df = df.join(pd.DataFrame({"Tendência": dict([(serie[-1][0], serie[-1][1])] + tend["proximos"])}), how="outer")
    st.line_chart(df.sort_index(), height=300)
    if tend["ok"]:
        k1, k2, k3 = st.columns(3)
        k1.metric("Direção", tend["direcao"].capitalize())
        k2.metric("Variação no último mês", "—" if tend["variacao_ultimo_mes_pct"] is None else f'{tend["variacao_ultimo_mes_pct"]:.1f}%'.replace(".", ","))
        k3.metric(f'Tendência p/ {tend["proximos"][0][0][5:]}/{tend["proximos"][0][0][:4]}', valor_com_unidade(tend["proximos"][0][1], x["unidade"]))
        st.caption(f'{previsao.AVISO} Baseada em {tend["meses"]} meses.')
    else:
        st.caption(f'{tend["motivo"]} A linha de tendência aparece sozinha quando houver meses suficientes.')

    st.subheader("Comparar indicadores lado a lado")
    escolha = st.multiselect("Indicadores (mesma unidade)", list(rot), max_selections=3, key="pe_comp")
    if len(escolha) >= 2:
        sel = [rot[e] for e in escolha]
        if len({y["unidade"] for y in sel}) > 1:
            st.warning("Os indicadores escolhidos têm unidades diferentes (por exemplo, R$ e %). Escolha indicadores na mesma unidade para comparar.")
        else:
            tab = painel.tabela_series(hist, [y["id"] for y in sel])
            st.line_chart(pd.DataFrame.from_dict(tab, orient="index").rename(columns={y["id"]: f'{y["id"]} · {y["nome"]}' for y in sel}), height=300)
            st.caption("Lado a lado, sem recalcular: cada linha é o valor gravado pelo app de origem.")


corpo()
base.botao_atualizar()
