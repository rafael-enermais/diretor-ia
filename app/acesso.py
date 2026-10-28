# -*- coding: utf-8 -*-
"""Diretor.IA - controle de acesso FAIL-CLOSED.
Regra: so entra quem esta na tabela diretoria.acesso com ativo = true e papel valido (admin ou diretor). E-mail que nao esta na tabela NAO entra,
mesmo tendo login no Supabase (o pool de logins e compartilhado com outros apps). Erro de banco tambem NAO libera: quem chama bloqueia.
O app so le esta tabela; incluir ou desativar alguem e feito por quem administra o banco."""
from __future__ import annotations

ADMIN, DIRETOR = "admin", "diretor"
PAPEIS = (ADMIN, DIRETOR)


def normalizar_email(email) -> str:
    return (email or "").strip().lower()


def decidir_papel(linha) -> str | None:
    """linha = {'papel':..., 'ativo':...} ou None. Devolve o papel so se estiver ativo (True de verdade) e for conhecido; senao None (nega)."""
    if not linha:
        return None
    if linha.get("ativo") is not True:
        return None
    papel = linha.get("papel")
    return papel if papel in PAPEIS else None


def papel_do_usuario(banco, email) -> str | None:
    """Papel do e-mail ou None (sem acesso). Se o banco falhar, a excecao SOBE (quem chama nega o acesso e registra o erro)."""
    e = normalizar_email(email)
    if not e or "@" not in e:
        return None
    linhas = banco.consultar("SELECT papel, ativo FROM diretoria.acesso WHERE email = %s", (e,))
    return decidir_papel(linhas[0] if linhas else None)
