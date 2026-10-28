# -*- coding: utf-8 -*-
"""Diretor.IA - login por e-mail e senha (Supabase Auth). O app so valida a credencial e guarda o E-MAIL na sessao (nunca o token).
Quem pode ENTRAR e decidido depois, pela tabela diretoria.acesso (fail-closed; ver acesso.py). Secrets: SUPABASE_URL e SUPABASE_ANON_KEY
(chave anon/public, NUNCA a service_role). Atencao: o pool de logins do Supabase e compartilhado com outros apps."""
from __future__ import annotations

import time

import streamlit as st
from supabase import create_client

from acesso import normalizar_email
from versao import NOME_APP

CHAVE = "dir_usuario"


@st.cache_resource(show_spinner=False)
def _cliente():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])
    except KeyError as exc:
        st.error(f"O secret `{exc.args[0]}` ainda não foi configurado (Settings → Secrets no Streamlit Cloud). Use a chave `anon`/`public`, nunca a `service_role`.")
        st.stop()
        return None


def sair() -> None:
    for k in [k for k in st.session_state if k.startswith("dir_") or k.startswith("_dir_")]:
        del st.session_state[k]


def require_login(registrar_falha=None) -> str:
    """Para a tela (st.stop) ate haver login valido. Devolve o e-mail (minusculo). registrar_falha: funcao sem argumentos chamada em login invalido."""
    if st.session_state.get(CHAVE):
        return st.session_state[CHAVE]
    cliente = _cliente()
    st.title(NOME_APP)
    st.subheader("Entrar")
    with st.form("login_diretor", clear_on_submit=False):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviou = st.form_submit_button("Entrar", type="primary")
    if enviou:
        if not email.strip() or not senha:
            st.error("Informe o e-mail e a senha.")
        else:
            try:
                resp = cliente.auth.sign_in_with_password({"email": email.strip(), "password": senha})
                usuario = normalizar_email(resp.user.email)
                if not usuario:
                    raise ValueError("resposta sem e-mail")
                st.session_state[CHAVE] = usuario
                st.rerun()
            except Exception:                                   # noqa: BLE001
                time.sleep(1)                                   # freia tentativa em sequencia
                if registrar_falha:
                    registrar_falha()
                st.error("E-mail ou senha inválidos.")          # mensagem unica: nao diz qual dos dois errou
    st.stop()
    return ""
