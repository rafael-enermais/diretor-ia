# -*- coding: utf-8 -*-
"""Diretor.IA - SUGESTAO de vinculo entre um item de report/pendencia e um indicador (I##) ou entregavel (E##) do catalogo.
Regra de ouro: este modulo SO' SUGERE. Nada e' gravado sem o usuario confirmar na tela (e o que ele recusar nao volta a ser sugerido).
Como sugere (simples e explicavel, sem IA): (1) codigo citado no texto (ex.: "I27", "E12") = confianca alta; (2) nome do item aparece inteiro no texto = alta;
(3) varias palavras do nome aparecem no texto = media. Puro: sem Streamlit e sem banco."""
from __future__ import annotations

import re
import unicodedata

_COD = re.compile(r"(?<![A-Za-z0-9])([IE])[-\s]?(\d{2})(?![0-9A-Za-z])")          # so' maiusculas: "I27", "E-12"; "e 12" (conjuncao) nao conta
_PARADAS = {"para", "como", "pelo", "pela", "pelos", "pelas", "dos", "das", "com", "sem", "por", "uma", "uns", "que", "nos", "nas", "ate", "mais", "menos", "total",
            "valor", "mensal", "geral", "gestao", "indice", "taxa", "controle"}
MIN_PALAVRAS = 2
MIN_FRACAO = 0.6


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").lower()


def _palavras(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", _sem_acento(s)) if w not in _PARADAS}


def valido(vid) -> bool:
    return bool(re.fullmatch(r"[IE]\d{2}", str(vid or "")))


def recusados(texto) -> set:
    return {x for x in str(texto or "").split(",") if valido(x)}


def sugerir(texto: str, catalogo: list, recusados_: set | None = None, limite: int = 3) -> list:
    """[{'item_id','nome','tipo','confianca':'alta'|'media','motivo'}] em ordem de confianca; ignora o que o usuario ja recusou."""
    recusados_ = recusados_ or set()
    por_id = {i["item_id"]: i for i in catalogo if i.get("item_id")}
    achados: dict = {}
    for letra, num in _COD.findall(texto or ""):
        vid = f"{letra}{num}"
        if vid in por_id and vid not in recusados_:
            achados[vid] = {"item_id": vid, "nome": por_id[vid].get("nome"), "tipo": por_id[vid].get("tipo"), "confianca": "alta", "motivo": f"o texto cita «{vid}»"}
    txt_norm = " " + re.sub(r"[^a-z0-9]+", " ", _sem_acento(texto)) + " "
    pal_texto = _palavras(texto)
    for vid, i in por_id.items():
        if vid in achados or vid in recusados_:
            continue
        nome_norm = " " + re.sub(r"[^a-z0-9]+", " ", _sem_acento(i.get("nome"))).strip() + " "
        if len(nome_norm.strip()) >= 6 and nome_norm in txt_norm:
            achados[vid] = {"item_id": vid, "nome": i.get("nome"), "tipo": i.get("tipo"), "confianca": "alta", "motivo": "o nome do item aparece no texto"}
            continue
        pal_nome = _palavras(i.get("nome"))
        comuns = pal_nome & pal_texto
        if len(comuns) >= MIN_PALAVRAS and len(comuns) / max(len(pal_nome), 1) >= MIN_FRACAO:
            achados[vid] = {"item_id": vid, "nome": i.get("nome"), "tipo": i.get("tipo"), "confianca": "media", "motivo": "palavras em comum: " + ", ".join(sorted(comuns))}
    ordem = sorted(achados.values(), key=lambda a: (0 if a["confianca"] == "alta" else 1, a["item_id"]))
    return ordem[:limite]


def rotulo(vid, catalogo: list) -> str:
    """'I27 · Contas a pagar' (ou so' o codigo se o item nao esta no catalogo; vazio -> '')."""
    if not vid:
        return ""
    i = next((x for x in catalogo if x.get("item_id") == vid), None)
    return f"{vid} · {i.get('nome')}" if i else str(vid)
