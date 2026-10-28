# -*- coding: utf-8 -*-
"""Diretor.IA - prontidao: quantos indicadores ja tem fonte pronta e quantos ja estao recebendo dado. Puro (sem Streamlit, sem banco)."""
from __future__ import annotations

import catalogo
import metricas_dados as md

SITUACOES = ["Existe no app", "Parcial", "Falta construir", "Input manual", "Sem definição"]


def situacao_chave(texto) -> str:
    """Texto da matriz ('Existe no app (conferir regra)', 'Parcial (calcular ou ligar)'...) -> uma das 5 chaves."""
    t = (texto or "").strip().lower()
    if t.startswith("existe"):
        return "Existe no app"
    if t.startswith("parcial"):
        return "Parcial"
    if t.startswith("falta"):
        return "Falta construir"
    if t.startswith("input"):
        return "Input manual"
    return "Sem definição"


def por_situacao(itens, por_item: dict) -> list:
    """Uma linha por situacao: quantos indicadores e quantos desses ja tem valor."""
    ind = catalogo.indicadores(itens)
    saida = []
    for sit in SITUACOES:
        grupo = [i for i in ind if situacao_chave(i.get("situacao")) == sit]
        com = sum(1 for i in grupo if md.status_do_item(por_item.get(i["item_id"], [])) != "Sem lançamento")
        saida.append({"Situação": sit, "Indicadores": len(grupo), "Já recebendo dado": com})
    return saida


def apps_da_fonte(texto) -> list:
    """'GDF (aba Obras)' -> ['GDF'];  'GDF + EGC + Dexie' -> ['GDF', 'EGC', 'Dexie'];  'Novo (hoje sem sistema)' -> ['Novo'];  vazio -> ['Sem definição'].
    Tira o que esta entre parenteses (aba/detalhe) para agrupar pelo app, nao pelo texto livre da matriz."""
    import re
    t = re.sub(r"\([^)]*\)", " ", str(texto or ""))
    partes = [p.strip(" .") for p in re.split(r"\s*(?:\+|/|;|,)\s*", t) if p.strip(" .")]
    partes = [p for p in partes if p not in ("—", "-")]
    return list(dict.fromkeys(partes)) or ["Sem definição"]


def por_fonte(itens, por_item: dict) -> list:
    """Uma linha por app/sistema de origem. Um indicador que depende de mais de um app aparece em cada um deles."""
    ind = catalogo.indicadores(itens)
    grupos: dict = {}
    for i in ind:
        for app in apps_da_fonte(i.get("app_origem")):
            grupos.setdefault(app, []).append(i)
    saida = []
    for fonte, grupo in sorted(grupos.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        com = sum(1 for i in grupo if md.status_do_item(por_item.get(i["item_id"], [])) != "Sem lançamento")
        saida.append({"App / sistema": fonte, "Indicadores": len(grupo), "Já recebendo dado": com})
    return saida


def sem_dado_ainda(itens, por_item: dict) -> list:
    """Indicadores sem nenhum valor gravado: lista curta (ID, nome, situacao) para o Diretor ver o que falta chegar."""
    return [{"ID": i["item_id"], "Indicador": i["nome"], "Situação no app": i.get("situacao") or "—", "Fonte do dado": i.get("fonte") or "—"}
            for i in catalogo.indicadores(itens) if md.status_do_item(por_item.get(i["item_id"], [])) == "Sem lançamento"]
