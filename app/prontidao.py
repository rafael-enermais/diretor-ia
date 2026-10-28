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


def por_fonte(itens, por_item: dict) -> list:
    """Uma linha por 'app/sistema candidato' (texto da matriz): quantos indicadores dependem dele e quantos ja recebem dado."""
    ind = catalogo.indicadores(itens)
    grupos: dict = {}
    for i in ind:
        grupos.setdefault((i.get("app_origem") or "—").strip(), []).append(i)
    saida = []
    for fonte, grupo in sorted(grupos.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        com = sum(1 for i in grupo if md.status_do_item(por_item.get(i["item_id"], [])) != "Sem lançamento")
        saida.append({"App / sistema": fonte, "Indicadores": len(grupo), "Já recebendo dado": com})
    return saida


def sem_dado_ainda(itens, por_item: dict) -> list:
    """Indicadores sem nenhum valor gravado: lista curta (ID, nome, situacao) para o Diretor ver o que falta chegar."""
    return [{"ID": i["item_id"], "Indicador": i["nome"], "Situação no app": i.get("situacao") or "—", "Fonte do dado": i.get("fonte") or "—"}
            for i in catalogo.indicadores(itens) if md.status_do_item(por_item.get(i["item_id"], [])) == "Sem lançamento"]
