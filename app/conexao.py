# -*- coding: utf-8 -*-
"""Diretor.IA - conexao com o Supabase pelo login unico do app (role app_diretoria). Nunca postgres/service_role."""
from __future__ import annotations

import psycopg2
import streamlit as st

from banco import Banco
from logs_app import mascarar, novo_codigo_erro

ROLE_DO_APP = "app_diretoria"


class ConexaoInvalida(Exception):
    """A DATABASE_URL conecta com o usuario errado (mensagem em linguagem simples)."""


def preparar(banco: Banco) -> str:
    """Fixa o schema `diretoria` na sessao (o pooler nao repassa o ajuste de search_path feito na role) e confere que o usuario conectado
    e a role do app. Devolve o usuario."""
    banco.executar("SET search_path TO diretoria")
    usuario = banco.consultar("SELECT current_user AS u")[0]["u"]
    if usuario != ROLE_DO_APP:
        raise ConexaoInvalida(
            f"A DATABASE_URL está conectando com um usuário que não é o do app (`{usuario}`). O app só pode usar `{ROLE_DO_APP}` "
            f"(no pooler: `{ROLE_DO_APP}.<ref-do-projeto>`). Ajuste o secret `DATABASE_URL`.")
    return usuario


@st.cache_resource(show_spinner=False)
def _abrir() -> Banco:
    url = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = True
    banco = Banco(conn)
    try:
        preparar(banco)
    except Exception:
        conn.close()
        raise
    return banco


def get_banco() -> Banco:
    """Banco do app. Se a conexao guardada caiu, abre outra sozinha. Se nao der, mostra aviso simples (sem traceback) e para a tela."""
    try:
        banco = _abrir()
        if not banco.viva():
            _abrir.clear()
            banco = _abrir()
        return banco
    except ConexaoInvalida as exc:
        st.error(str(exc))
    except KeyError:
        st.error("O secret `DATABASE_URL` ainda não foi configurado (Settings → Secrets no Streamlit Cloud).")
    except Exception as exc:                                    # noqa: BLE001
        codigo = novo_codigo_erro()
        print(f"[{codigo}] falha ao conectar no banco: {type(exc).__name__}: {mascarar(exc, 300)}")   # vai para o log do Streamlit (ja sem endereco/senha)
        st.error(f"Não consegui conectar ao banco agora. Tente de novo em instantes. Se continuar, informe o código **{codigo}**.")
    st.stop()
    return None                                                 # nunca chega aqui
