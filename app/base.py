# -*- coding: utf-8 -*-
"""Diretor.IA - pecas comuns das telas: papel do usuario (fail-closed), carga dos dados (cache curto), erro com codigo, rodape com a versao."""
from __future__ import annotations

import html

import streamlit as st

import acesso
import catalogo
import logs_app
import metricas_dados as md
from conexao import get_banco
from versao import APP_VERSION, NOME_APP

CACHE_SEGUNDOS = 60          # "quase tempo real": o painel relê o banco no maximo a cada 60 s (botao Atualizar força na hora)


def resolver_papel(email: str) -> str:
    """Decide se o e-mail entra. SEM papel ativo em diretoria.acesso (ou erro de banco) => NAO entra (st.stop). Chamado pelo app.py depois do login."""
    banco = get_banco()
    try:
        papel = acesso.papel_do_usuario(banco, email)
    except Exception as exc:                                    # noqa: BLE001  (banco falhou: NAO libera)
        codigo = logs_app.registrar_erro(banco, "acesso", "verificar_acesso", exc, usuario=email)
        st.error(f"Não foi possível verificar o seu acesso agora. Tente de novo em instantes. Se continuar, informe o código **{codigo}**.")
        _botao_sair()
        st.stop()
        return ""
    if papel is None:
        if not st.session_state.get("_dir_negado_logado"):
            logs_app.registrar(banco, "aviso", "acesso", "acesso_negado", "Usuário autenticado sem acesso ao painel", usuario=email)
            st.session_state["_dir_negado_logado"] = True
        st.error("Este usuário não tem acesso ao Diretor.IA. Se precisa de acesso, peça a quem administra o painel.")
        _botao_sair()
        st.stop()
        return ""
    st.session_state["dir_papel"] = papel
    if not st.session_state.get("_dir_login_logado"):
        logs_app.registrar(banco, "evento", "acesso", "login", "Login no painel", usuario=email, contexto={"papel": papel})
        st.session_state["_dir_login_logado"] = True
    return papel


def _botao_sair() -> None:
    import auth
    if st.sidebar.button("Sair"):
        auth.sair()
        st.rerun()


def contexto():
    """(banco, usuario, papel) para as telas. Se a sessao nao passou pela checagem de acesso do app.py, para a tela."""
    usuario, papel = st.session_state.get("dir_usuario"), st.session_state.get("dir_papel")
    if not usuario or papel not in acesso.PAPEIS:
        st.error("Sua sessão não foi validada. Recarregue a página e entre de novo.")
        st.stop()
    return get_banco(), usuario, papel


def exigir_admin(papel: str) -> None:
    if papel != acesso.ADMIN:
        st.error("Esta tela é só para o administrador do painel.")
        st.stop()


def falha(banco, tela: str, acao: str, exc: Exception, usuario: str) -> None:
    """Mostra erro em linguagem simples com codigo (nunca o traceback), registra no log e para a tela."""
    codigo = logs_app.registrar_erro(banco, tela, acao, exc, usuario=usuario)
    st.error(f"Algo deu errado ao carregar esta tela. Informe o código **{codigo}** a quem administra o painel.")
    st.stop()


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def _carregar(_banco, chave: int):
    itens = catalogo.carregar(_banco)
    atuais = md.ler_atuais(_banco)
    return itens, atuais


def carregar_painel(banco, tela: str, usuario: str):
    """(itens do catalogo, linhas atuais das metricas, {item_id: linhas}). Cache de 60 s; erro => mensagem com codigo."""
    try:
        itens, atuais = _carregar(banco, st.session_state.get("_dir_refresh", 0))
    except Exception as exc:                                    # noqa: BLE001
        falha(banco, tela, "carregar_painel", exc, usuario)
        return [], [], {}
    return itens, atuais, md.agrupar_por_item(atuais)


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def _historico(_banco, chave: int):
    return md.ler_historico_geral(_banco)


def carregar_historico(banco, tela: str, usuario: str) -> list:
    """Historico mensal de todos os itens (cache de 60 s). Erro => mensagem com codigo."""
    try:
        return _historico(banco, st.session_state.get("_dir_refresh", 0))
    except Exception as exc:                                    # noqa: BLE001
        falha(banco, tela, "carregar_historico", exc, usuario)
        return []


def segredo(nome: str) -> str:
    """Valor de um secret (ou vazio). Nunca mostrar na tela."""
    try:
        return str(st.secrets[nome]).strip()
    except Exception:                                           # noqa: BLE001
        return ""


def botao_atualizar() -> None:
    if st.button("Atualizar agora", help="Relê o banco (o painel já se atualiza sozinho a cada 1 minuto)."):
        st.session_state["_dir_refresh"] = st.session_state.get("_dir_refresh", 0) + 1
        st.rerun()


def rodape() -> None:
    """Nome do app + versao no pe do menu lateral (confira a versao depois de cada Reboot)."""
    st.sidebar.markdown(f'<div class="dir-rodape">{html.escape(NOME_APP)} · v{html.escape(APP_VERSION)}</div>', unsafe_allow_html=True)
