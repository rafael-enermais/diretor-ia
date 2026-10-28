# -*- coding: utf-8 -*-
"""Diretor.IA - Logs do app (SO administrador). Erros com codigo, avisos e eventos de funcionamento (login, gravacoes). Sem senha/token/chave (mascarados na gravacao)."""
import pandas as pd
import streamlit as st

import base
import logs_app
from fuso import fmt_br

banco, usuario, papel = base.contexto()
base.exigir_admin(papel)
st.title("Logs do app")
st.caption("Só o administrador vê esta tela. Nada é apagado por aqui.")

c1, c2, c3, c4 = st.columns(4)
dias = c1.selectbox("Período", [1, 7, 30, 90, 365], index=2, format_func=lambda d: f"últimos {d} dia(s)")
nivel = c2.selectbox("Nível", ["(todos)", "erro", "aviso", "evento"])
quem = c3.text_input("Usuário contém", max_chars=80)
cod = c4.text_input("Código de erro", max_chars=30, placeholder="E-DIRETOR-AAMMDD-XXXX")

linhas = logs_app.listar(banco, dias=dias, nivel=None if nivel == "(todos)" else nivel, usuario=quem.strip() or None, codigo=cod.strip().upper() or None)
if not linhas:
    st.info("Nenhum registro para este filtro (ou a tabela de log ainda não existe).")
else:
    df = pd.DataFrame([{"Quando": fmt_br(l["criado_em"]), "Nível": l["nivel"], "Tela": l["tela"], "Ação": l["acao"], "Usuário": l["usuario"] or "—",
                        "Código": l["codigo_erro"] or "—", "Mensagem": l["mensagem"], "Versão": l["versao_app"]} for l in linhas])
    st.dataframe(df, hide_index=True, width="stretch")
    erros = [l for l in linhas if l["nivel"] == "erro"]
    if erros:
        with st.expander("Detalhe técnico dos erros (mais recentes)"):
            for l in erros[:20]:
                st.markdown(f'**{l["codigo_erro"] or "—"}** · {fmt_br(l["criado_em"])} · {l["tela"]}/{l["acao"]}')
                st.code(l["detalhe"] or "—", language="text")
    st.caption(f"{len(linhas)} registro(s) (máximo 500 por consulta).")
base.botao_atualizar()
