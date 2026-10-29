# -*- coding: utf-8 -*-
"""Diretor.IA - Relatorios: gera o PDF da Diretoria Financeira (mesmo visual do EGC e do GDF: logo, fundo, capa, rodape). O texto vem de modelo fixo preenchido
com os numeros do painel; nenhuma IA escreve o relatorio e nada e' recalculado. O PDF fica so' na memoria (nao e' gravado em lugar nenhum) e e' baixado por voce."""
import streamlit as st

import base
import catalogo
import logs_app
import relatorio_dados as RD
import reports
from fuso import agora_br

banco, usuario, papel = base.contexto()
st.title("Relatórios")
st.caption("Gera o relatório em PDF com o mesmo visual dos relatórios do EGC e do GDF. Os números são os que o painel já mostra; nada é recalculado e nenhuma IA escreve o texto.")

itens, atuais, por_item = base.carregar_painel(banco, "relatorios", usuario)
if not itens:
    st.warning("O catálogo ainda não foi carregado no banco; não há o que reportar.")
    st.stop()

pend_ok = False
try:
    pend_ok = reports.instalado(banco)
except Exception:                                               # noqa: BLE001  (sem a tabela de reports o relatorio sai sem essa secao)
    pend_ok = False

st.subheader("O que entra no relatório")
escolhidas = st.multiselect("Seções", list(RD.SECOES), default=[s for s in RD.SECOES if s != "pendencias" or pend_ok],
                            format_func=lambda k: RD.SECOES[k])
if "pendencias" in escolhidas and not pend_ok:
    st.info("As pendências ainda não estão ligadas no banco (SQL-04/SQL-05); essa seção sairá vazia.")

ind = [i for i in catalogo.indicadores(itens) if por_item.get(i["item_id"])]
pedidos = []
if "detalhes" in escolhidas:
    pedidos = st.multiselect(f"Indicadores no detalhe (até {RD.MAX_DETALHES}; vazio = o app escolhe os fora da meta, em atenção ou com aviso de número fora do comum)",
                             [i["item_id"] for i in ind], format_func=lambda k: f"{k} · " + next((i["nome"] for i in ind if i["item_id"] == k), ""))
    if len(pedidos) > RD.MAX_DETALHES:
        st.warning(f"Só os {RD.MAX_DETALHES} primeiros entram no detalhe.")
obs = st.text_area("Observação sua (opcional; sai no resumo)", max_chars=2000, height=90)

if st.button("Gerar relatório", type="primary", disabled=not escolhidas):
    try:
        import relatorio_pdf as RP                               # so' carrega o gerador quando precisa
        hist = base.carregar_historico(banco, "relatorios", usuario) if "detalhes" in escolhidas else []
        itens_pend = reports.listar(banco) if (pend_ok and "pendencias" in escolhidas) else None
        agora = agora_br()
        ctx = RD.montar(itens, por_item, hist, itens_pend, {"secoes": escolhidas, "detalhe_ids": pedidos[:RD.MAX_DETALHES], "observacao": obs}, agora)
        st.session_state["rel_pdf"] = (RP.gerar_pdf(ctx), agora.strftime("%Y-%m-%d_%H%M"))
        logs_app.registrar(banco, "evento", "relatorios", "gerar_pdf", "Relatório PDF gerado", detalhe=f"secoes={','.join(escolhidas)}; detalhes={len(ctx['detalhes'])}", usuario=usuario)
    except Exception as exc:                                    # noqa: BLE001
        st.session_state.pop("rel_pdf", None)
        base.falha(banco, "relatorios", "gerar_pdf", exc, usuario)

if st.session_state.get("rel_pdf"):
    dados, carimbo = st.session_state["rel_pdf"]
    st.success(f"Relatório pronto ({len(dados) / 1024:.0f} KB).")
    st.download_button("⬇️ Baixar PDF", data=dados, file_name=f"relatorio_diretoria_{carimbo}.pdf", mime="application/pdf")
st.caption("Referência de data: posição de cada indicador no último lançamento dos apps de origem. O PDF não é guardado no painel; para outro, gere de novo.")
base.botao_atualizar()
