# -*- coding: utf-8 -*-
"""Diretor.IA - leitura das metricas ja calculadas pelo GDF (visoes diretoria.metricas_atual e diretoria.metricas). O app NAO recalcula nada:
mostra o valor gravado, o status que o GDF decidiu e a data da gravacao. Quando um item tem varias linhas (empresa/obra/UN), mostra as linhas; nao soma."""
from __future__ import annotations

PRIORIDADE = ["Fora da meta", "Atenção", "No alvo", "Sem meta", "Sem lançamento"]       # do pior para o melhor
# "Sem meta" = ha valor gravado, mas o GDF nao tem meta numerica para julgar (indicador informativo): conta como COM valor.

_SQL_ATUAL = """SELECT item_id, indicador, dono, unidade, periodo, empresa, obra, un, app_origem, meta, previsto, realizado,
                       numerador, denominador, pct_atingimento, status, origem, detalhe, atualizado_em
                FROM diretoria.metricas_atual ORDER BY item_id, empresa, obra, un"""
_SQL_HIST = """SELECT item_id, periodo, empresa, obra, un, app_origem, unidade, meta, previsto, realizado, pct_atingimento, status, origem, atualizado_em
               FROM diretoria.metricas WHERE item_id = %s ORDER BY periodo DESC, empresa, obra, un LIMIT 240"""


def ler_atuais(banco) -> list:
    return banco.consultar(_SQL_ATUAL)


def ler_historico(banco, item_id: str) -> list:
    return banco.consultar(_SQL_HIST, (item_id,))


def agrupar_por_item(linhas) -> dict:
    """{item_id: [linhas]}"""
    saida: dict = {}
    for l in linhas:
        saida.setdefault(l.get("item_id"), []).append(l)
    return saida


def tem_valor(linha) -> bool:
    """True se a linha tem numero gravado (realizado ou numerador), mesmo sem meta para julgar."""
    return any(linha.get(k) is not None for k in ("realizado", "numerador"))


def status_do_item(linhas) -> str:
    """Status unico do item: o PIOR entre as linhas (Fora da meta > Atencao > No alvo). Se nenhuma linha tem status de meta mas ha valor gravado: 'Sem meta'
    (informativo). Sem linha ou sem valor: 'Sem lançamento'."""
    linhas = linhas or []
    achados = {l.get("status") for l in linhas}
    for s in ("Fora da meta", "Atenção", "No alvo"):
        if s in achados:
            return s
    return "Sem meta" if any(tem_valor(l) for l in linhas) else "Sem lançamento"


def periodo_recente(linhas) -> str | None:
    ps = [l.get("periodo") for l in (linhas or []) if l.get("periodo")]
    return max(ps) if ps else None


def ultima_atualizacao(linhas):
    datas = [l.get("atualizado_em") for l in (linhas or []) if l.get("atualizado_em")]
    return max(datas) if datas else None


def contar_status(status_lista) -> dict:
    """{'No alvo': n, 'Atenção': n, 'Fora da meta': n, 'Sem lançamento': n}"""
    c = {s: 0 for s in PRIORIDADE}
    for s in status_lista:
        c[s if s in c else "Sem lançamento"] += 1
    return c


def periodo_br(periodo) -> str:
    """'2026-09' -> '09/2026'; vazio -> '—'."""
    p = str(periodo or "")
    return f"{p[5:7]}/{p[:4]}" if len(p) == 7 and p[4] == "-" else "—"
