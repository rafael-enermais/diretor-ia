# -*- coding: utf-8 -*-
"""Diretor.IA - Assistente (chat IA, N1, SOMENTE LEITURA). Padrao Dexie do GDF: ferramentas fechadas, resposta conferida, memoria por usuario (SQL-03), sem links/imagens."""
import time

import pandas as pd
import streamlit as st

import base
import graficos
import chat_core as CC
import chat_ferramentas as FERR
import chat_memoria as MEM
import logs_app

banco, usuario, papel = base.contexto()
st.title("Assistente")
st.caption("Pergunte sobre indicadores, entregáveis, o que está fora da meta e para onde um número caminha. Só lê o que o painel já mostra; não grava nem altera nada.")

chave = base.segredo("ANTHROPIC_API_KEY")
modelo = base.segredo("ANTHROPIC_MODEL") or CC.MODELO_PADRAO
if not chave:
    st.warning("A chave da IA ainda não está configurada. Cadastre o secret **ANTHROPIC_API_KEY** em Settings → Secrets do Streamlit Cloud e reinicie o app.")
    st.stop()


@st.cache_resource(show_spinner=False)
def _cliente():
    import anthropic
    return anthropic.Anthropic(api_key=base.segredo("ANTHROPIC_API_KEY"), timeout=60.0, max_retries=1)


S = st.session_state
if "dir_chat_msgs" not in S:
    S["dir_chat_inst"] = MEM.instalado(banco)
    S["dir_chat_msgs"] = MEM.carregar(banco, usuario) if S["dir_chat_inst"] else []
    S["dir_chat_estado"] = CC.novo_estado()
    S["dir_chat_n"] = 0
msgs, estado, inst = S["dir_chat_msgs"], S["dir_chat_estado"], S["dir_chat_inst"]

if not inst:
    st.info("A conversa vale só enquanto esta página estiver aberta. Para ela continuar quando você voltar, quem administra o banco precisa rodar o SQL-03 (tabelas do chat).")

topo = st.columns([1, 1, 4])
if topo[0].button("Nova conversa", help="Arquiva a conversa atual e começa limpa (nada é apagado)."):
    if inst:
        MEM.arquivar(banco, usuario)
    S["dir_chat_msgs"], S["dir_chat_estado"] = [], CC.novo_estado()
    st.rerun()

EXEMPLOS = ["Qual é a situação geral dos indicadores hoje?", "O que está fora da meta ou em atenção?", "Mostre a evolução e a tendência do I22.", "Quais entregáveis têm prazo no dia 7?"]
pendente = None
if not msgs:
    st.markdown("**Sugestões:**")
    cols = st.columns(2)
    for k, ex in enumerate(EXEMPLOS):
        if cols[k % 2].button(ex, key=f"ex_{k}"):
            pendente = ex

for m in msgs:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"].replace("$", "\\$"))


def desenhar_grafico(g, tabela):
    if not (g and tabela):
        return
    df = pd.DataFrame(tabela).set_index(g["x"])[g["y"]]
    if g.get("titulo"):
        st.caption(g["titulo"])
    if g["tipo"] == "linhas":
        graficos.mostrar_linhas(df, altura=280)
    else:
        graficos.mostrar_barras(df, altura=280, horizontal=g["tipo"] == "barras_horizontais")


desenhar_grafico(estado.get("grafico"), estado.get("ultima_tabela"))

digitada = st.chat_input("Pergunte ao assistente…", max_chars=CC.MAX_PERGUNTA)  # sempre desenhada (v0.2.1): antes, clicar numa sugestão escondia a caixa
pergunta = pendente or digitada
if pergunta:
    limite_ok = (MEM.perguntas_hoje(banco, usuario) < MEM.LIMITE_PERGUNTAS_DIA) if inst else (S["dir_chat_n"] < 40)
    if not limite_ok:
        st.warning("Você atingiu o limite de perguntas por dia para controlar o custo da IA. Volte amanhã ou fale com quem administra o painel.")
        st.stop()
    with st.chat_message("user"):
        st.markdown(pergunta.replace("$", "\\$"))
    with st.chat_message("assistant"):
        with st.spinner("Consultando os dados…"):
            itens, atuais, por_item = base.carregar_painel(banco, "assistente", usuario)
            ctx = FERR.Contexto(banco, itens, por_item, historico_geral=base.carregar_historico(banco, "assistente", usuario))
            t0 = time.time()
            res = CC.responder(_cliente(), ctx, modelo, msgs, pergunta, estado)
            ms = int((time.time() - t0) * 1000)
        st.markdown(res["texto"].replace("$", "\\$"))
        desenhar_grafico(estado.get("grafico"), estado.get("ultima_tabela"))
        if res.get("ferramentas"):
            st.caption("Consultei: " + ", ".join(dict.fromkeys(res["ferramentas"])))
    S["dir_chat_n"] += 1
    if res["ok"]:
        msgs.append({"role": "user", "content": pergunta})
        msgs.append({"role": "assistant", "content": res["texto"]})
        S["dir_chat_msgs"] = msgs[-CC.MAX_HISTORICO * 2:]
        if inst:
            MEM.gravar(banco, usuario, "user", pergunta)
            MEM.gravar(banco, usuario, "assistant", res["texto"])
    if inst:
        MEM.registrar_pergunta(banco, usuario, pergunta, res, modelo, ms)
    if res.get("erro"):
        logs_app.registrar(banco, "aviso", "assistente", "erro_ia", "Falha ao responder pela IA", detalhe=res["erro"], usuario=usuario)
    else:
        logs_app.registrar(banco, "evento", "assistente", "pergunta", "Pergunta ao assistente", usuario=usuario,
                           contexto={"ferramentas": res.get("ferramentas"), "conferir": res.get("conferir"), "tokens_entrada": res.get("tokens_entrada"), "tokens_saida": res.get("tokens_saida")})
