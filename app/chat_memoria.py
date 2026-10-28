# -*- coding: utf-8 -*-
"""Diretor.IA - memoria do chat (tabelas diretoria.chat_mensagem e diretoria.chat_pergunta_log, SQL-03). Guarda so' o TEXTO da pergunta/resposta por usuario;
ao abrir a tela le as ultimas JANELA mensagens nao arquivadas. 'Nova conversa' arquiva (nada e' apagado). Se o SQL-03 ainda nao foi rodado, tudo aqui vira
no-op e a conversa fica so' na sessao (a tela avisa). Nunca derruba a tela."""
from __future__ import annotations

JANELA = 24
MAX_CONTEUDO = 6000
LIMITE_PERGUNTAS_DIA = 60          # por usuario, por dia (trava de custo; vale quando o SQL-03 existe; sem ele, o limite e' da sessao)


def instalado(banco) -> bool:
    try:
        r = banco.consultar("SELECT to_regclass('diretoria.chat_mensagem') IS NOT NULL AS a, to_regclass('diretoria.chat_pergunta_log') IS NOT NULL AS b")
        return bool(r and r[0]["a"] and r[0]["b"])
    except Exception:                                           # noqa: BLE001
        return False


def carregar(banco, usuario: str, limite: int = JANELA) -> list:
    if not usuario:
        return []
    try:
        linhas = banco.consultar(
            """SELECT papel, conteudo FROM (SELECT id, papel, conteudo FROM diretoria.chat_mensagem WHERE usuario = %s AND NOT arquivado ORDER BY id DESC LIMIT %s) x ORDER BY id""",
            (usuario.strip().lower(), int(limite)))
        return [{"role": l["papel"], "content": l["conteudo"]} for l in linhas]
    except Exception:                                           # noqa: BLE001
        return []


def gravar(banco, usuario: str, papel: str, conteudo: str) -> bool:
    if not usuario or papel not in ("user", "assistant") or not (conteudo or "").strip():
        return False
    try:
        banco.executar("INSERT INTO diretoria.chat_mensagem (usuario, papel, conteudo) VALUES (%s,%s,%s)", (usuario.strip().lower(), papel, conteudo[:MAX_CONTEUDO]))
        return True
    except Exception:                                           # noqa: BLE001
        return False


def arquivar(banco, usuario: str) -> bool:
    """Encerra a conversa atual (marca arquivado; nada e' apagado)."""
    try:
        banco.executar("UPDATE diretoria.chat_mensagem SET arquivado = true WHERE usuario = %s AND NOT arquivado", (usuario.strip().lower(),))
        return True
    except Exception:                                           # noqa: BLE001
        return False


def perguntas_hoje(banco, usuario: str) -> int:
    """Quantas perguntas o usuario ja fez hoje (hora de Brasilia). 0 se nao da' para saber."""
    try:
        r = banco.consultar("""SELECT count(*) AS n FROM diretoria.chat_pergunta_log
                               WHERE usuario = %s AND (criado_em AT TIME ZONE 'America/Sao_Paulo')::date = (now() AT TIME ZONE 'America/Sao_Paulo')::date""",
                            (usuario.strip().lower(),))
        return int(r[0]["n"])
    except Exception:                                           # noqa: BLE001
        return 0


def registrar_pergunta(banco, usuario: str, pergunta: str, resultado: dict, modelo: str, duracao_ms: int) -> bool:
    """Uma linha por pergunta: quem, quando, ferramentas, tokens e motivo tecnico do erro (sem chaves). Guarda so' o comeco da pergunta (300)."""
    try:
        banco.executar(
            """INSERT INTO diretoria.chat_pergunta_log (usuario, pergunta, ferramentas, modelo, tokens_entrada, tokens_saida, duracao_ms, ok, conferir, erro_tecnico)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (usuario.strip().lower(), (pergunta or "")[:300], list(resultado.get("ferramentas") or []), (modelo or "")[:80], int(resultado.get("tokens_entrada") or 0),
             int(resultado.get("tokens_saida") or 0), int(duracao_ms), bool(resultado.get("ok")), int(resultado.get("conferir") or 0), (resultado.get("erro") or "")[:300] or None))
        return True
    except Exception:                                           # noqa: BLE001
        return False
