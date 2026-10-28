# -*- coding: utf-8 -*-
"""Diretor.IA - log de erros e de funcionamento do proprio app (padrao PADRAO-OPERABILIDADE).
Escreve em diretoria.app_log pela funcao diretoria.registrar_log. Codigo de erro mostrado ao usuario: E-DIRETOR-AAMMDD-xxxx.
REGRA DE OURO: registrar log NUNCA derruba o app (tudo em try/except). Nunca registrar senha, token, chave, endereco de banco, CPF."""
from __future__ import annotations

import json
import re
import secrets
import traceback

from fuso import agora_br
from texto import limpar_texto
from versao import APP_VERSION

_SENSIVEL = ("senha", "password", "token", "apikey", "api_key", "secret", "authorization", "cpf", "database_url", "key")
_PADROES = [
    (re.compile(r"postgres(ql)?://\S+", re.I), "[endereco-de-banco]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"), "[chave]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}(\.[A-Za-z0-9_\-]+)*"), "[token]"),
    (re.compile(r"\b(ghp_|github_pat_)[A-Za-z0-9_]{10,}"), "[token]"),
    (re.compile(r"Bearer\s+\S+", re.I), "Bearer [token]"),
    (re.compile(r"(password|senha|pwd)\s*[=:]\s*\S+", re.I), r"\1=[oculto]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[e-mail]"),
]


def novo_codigo_erro() -> str:
    """Codigo curto e unico: E-DIRETOR-AAMMDD-xxxx (4 hex maiusculos)."""
    return f"E-DIRETOR-{agora_br():%y%m%d}-{secrets.token_hex(2).upper()}"


def mascarar(texto, maximo: int = 4000) -> str:
    t = str(texto if texto is not None else "")
    for padrao, troca in _PADROES:
        t = padrao.sub(troca, t)
    return t[:maximo]


def _limpar_contexto(ctx):
    if isinstance(ctx, dict):
        saida = {}
        for k, v in ctx.items():
            if any(s in str(k).lower() for s in _SENSIVEL):
                saida[str(k)] = "***"
            else:
                saida[str(k)] = _limpar_contexto(v)
        return saida
    if isinstance(ctx, (list, tuple)):
        return [_limpar_contexto(x) for x in list(ctx)[:50]]
    if isinstance(ctx, (int, float, bool)) or ctx is None:
        return ctx
    return mascarar(ctx, 300)


def registrar(banco, nivel, tela, acao, mensagem, *, detalhe=None, contexto=None, codigo=None, usuario=None, correlacao=None) -> bool:
    """Grava uma linha de log. nivel: 'evento' | 'aviso' | 'erro'. Nunca levanta excecao. Devolve True se gravou."""
    try:
        if banco is None or nivel not in ("evento", "aviso", "erro"):
            return False
        ctx = json.dumps(_limpar_contexto(contexto or {}), ensure_ascii=False, default=str)
        banco.executar(
            "SELECT diretoria.registrar_log(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
            (nivel, APP_VERSION, limpar_texto(usuario, 200) if usuario else None, tela, acao, codigo,
             mascarar(mensagem, 1000), mascarar(detalhe, 4000) if detalhe else None, ctx, correlacao))
        return True
    except Exception:                                           # noqa: BLE001  (log nunca derruba o app)
        return False


def registrar_erro(banco, tela, acao, exc, *, usuario=None, contexto=None) -> str:
    """Registra o erro com codigo novo e devolve o codigo (para mostrar ao usuario). Mesmo sem banco, o codigo e devolvido."""
    codigo = novo_codigo_erro()
    try:
        resumo = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        quadros = traceback.extract_tb(exc.__traceback__)[-3:] if getattr(exc, "__traceback__", None) else []
        onde = " | ".join(f"{q.filename.split('/')[-1]}:{q.lineno} {q.name}" for q in quadros)
        detalhe = f"{resumo}\n{onde}"
    except Exception:                                           # noqa: BLE001
        detalhe = type(exc).__name__
    registrar(banco, "erro", tela, acao, "Erro no app", detalhe=detalhe, contexto=contexto, codigo=codigo, usuario=usuario)
    return codigo


def listar(banco, dias: int = 30, nivel=None, usuario=None, codigo=None, limite: int = 500) -> list:
    """Linhas mais recentes (so o admin ve esta tela; a trava e do app). Lista vazia se a tabela nao existe ainda."""
    try:
        return banco.consultar(
            """SELECT id, criado_em, nivel, versao_app, usuario, tela, acao, codigo_erro, mensagem, detalhe
               FROM diretoria.app_log
               WHERE criado_em >= now() - make_interval(days => %s)
                 AND (%s::text IS NULL OR nivel = %s)
                 AND (%s::text IS NULL OR usuario ILIKE %s)
                 AND (%s::text IS NULL OR codigo_erro = %s)
               ORDER BY id DESC LIMIT %s""",
            (int(dias), nivel, nivel, usuario, f"%{usuario}%" if usuario else None, codigo, codigo, min(int(limite), 2000)))
    except Exception:                                           # noqa: BLE001
        return []
