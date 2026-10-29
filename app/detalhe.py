# -*- coding: utf-8 -*-
"""Diretor.IA - DETALHE dos indicadores: transforma o campo `detalhe` que o app de origem (GDF, EGC...) grava junto do numero (JSON ou texto) em algo que o
Diretor le sem esforco: campos com rotulo, tabelas (ex.: faixas de atraso, com % do total) e avisos simples de "numero fora do comum".
Modulo PURO (sem Streamlit, sem banco). Nao recalcula indicador: so' formata o que o app de origem entregou e calcula percentuais de apresentacao
(parte / total das proprias linhas) e a variacao frente ao mes anterior. Os limites dos avisos ficam nas constantes abaixo (faceis de ajustar)."""
from __future__ import annotations

import json
import re

from formatacao import numero_br, valor_com_unidade

LIMITE_VARIACAO_PCT = 30.0      # aviso quando o valor mudou 30% ou mais frente ao mes anterior
LIMITE_FAIXA_90_PCT = 20.0      # aviso quando 20% ou mais do valor vencido esta ha mais de 90 dias

ROTULOS = {
    "posicao": "Posição dos dados", "venc_ate": "Vencidos até", "n_vencidos": "Títulos vencidos", "a_vencer_total": "A vencer (total)",
    "a_vencer_30d": "A vencer em 30 dias", "n_a_vencer_30d": "Títulos a vencer em 30 dias", "faixas": "Faixas de atraso",
    "prazo_medio_dias": "Prazo médio", "tela": "Onde ver no app de origem", "faixa": "Faixa de atraso", "n": "Títulos", "valor": "Valor",
}
_MOEDA = ("valor", "total", "vencer", "vencido", "saldo", "receita", "custo", "despesa", "previsto", "realizado", "carteira", "pago", "recebido", "bdi", "caixa")
_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def carregar(detalhe):
    """Texto/JSON/dict -> (dict|list|None, texto|None). JSON valido vira estrutura; qualquer outro texto fica como texto."""
    if detalhe is None or detalhe == "":
        return None, None
    if isinstance(detalhe, (dict, list)):
        return detalhe, None
    s = str(detalhe).strip()
    if s[:1] in "{[":
        try:
            return json.loads(s), None
        except ValueError:
            pass
    return None, s or None


def rotulo(chave) -> str:
    c = str(chave)
    return ROTULOS.get(c) or c.replace("_", " ").strip().capitalize()


def tipo_da_chave(chave: str) -> str:
    c = str(chave).lower()
    if c == "n" or c.startswith("n_") or c.endswith("_n") or "quantidade" in c or "qtd" in c:
        return "contagem"
    if "dias" in c or c.endswith("_dia"):
        return "dias"
    if "pct" in c or "percentual" in c or c.endswith("_perc"):
        return "pct"
    if any(m in c for m in _MOEDA):
        return "moeda"
    return "numero"


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def formatar(chave, v) -> str:
    """Valor de um campo do detalhe, no formato pelo tipo da chave (R$, dias, %, contagem, data dd/mm/aaaa)."""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, str):
        return f"{v[8:10]}/{v[5:7]}/{v[:4]}" if _DATA_ISO.match(v) else v
    n = _num(v)
    if n is None:
        return str(v)
    t = tipo_da_chave(chave)
    if t == "moeda":
        return valor_com_unidade(n, "R$")
    if t == "dias":
        return valor_com_unidade(n, "dias")
    if t == "pct":
        return numero_br(n, 1) + "%"
    if t == "contagem":
        return numero_br(n, 0)
    return numero_br(n, 0 if n == int(n) else 2)


def _tabela(chave, lista) -> dict | None:
    """Lista de dicts -> tabela pronta: 1a coluna de texto = rotulo da linha; contagens e valores formatados; '% do total' quando ha coluna de valor."""
    linhas = [l for l in lista if isinstance(l, dict)]
    if not linhas:
        return None
    chaves = list(linhas[0].keys())
    col_rot = next((k for k in chaves if all(isinstance(l.get(k), str) for l in linhas)), None)
    col_val = next((k for k in chaves if tipo_da_chave(k) == "moeda" and all(_num(l.get(k)) is not None for l in linhas)), None)
    total = sum(_num(l[col_val]) for l in linhas) if col_val else 0.0
    out, bruto = [], []
    for l in linhas:
        linha = {}
        if col_rot:
            linha[rotulo(col_rot)] = l.get(col_rot)
        for k in chaves:
            if k == col_rot:
                continue
            linha[rotulo(k)] = formatar(k, l.get(k))
        part = None
        if col_val and abs(total) > 0.005:
            part = round(100.0 * _num(l[col_val]) / total, 1)
            linha["% do total"] = numero_br(part, 1) + "%"
        out.append(linha)
        bruto.append({"rotulo": l.get(col_rot) if col_rot else None, "valor": _num(l.get(col_val)) if col_val else None, "parte_pct": part})
    return {"titulo": rotulo(chave), "linhas": out, "bruto": bruto, "total": total if col_val else None}


def interpretar(detalhe) -> dict:
    """{'texto': str|None, 'campos': [(rotulo, valor_formatado)], 'tabelas': [{titulo, linhas, bruto, total}]}"""
    estrutura, texto = carregar(detalhe)
    campos, tabelas = [], []
    if isinstance(estrutura, dict):
        for k, v in estrutura.items():
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                t = _tabela(k, v)
                if t:
                    tabelas.append(t)
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    if not isinstance(v2, (dict, list)):
                        campos.append((f"{rotulo(k)} › {rotulo(k2)}", formatar(k2, v2)))
            elif isinstance(v, list):
                campos.append((rotulo(k), ", ".join(str(x) for x in v) or "—"))
            elif v is not None:
                campos.append((rotulo(k), formatar(k, v)))
    elif isinstance(estrutura, list):
        t = _tabela("itens", estrutura)
        if t:
            tabelas.append(t)
    return {"texto": texto, "campos": campos, "tabelas": tabelas}


def composicao(linha: dict) -> str | None:
    """'R$ 4.362.789,11 de R$ 39.681.681,48 = 11,0%' a partir de numerador/denominador gravados pelo app de origem (None se nao der para dividir)."""
    num, den = _num(_f(linha.get("numerador"))), _num(_f(linha.get("denominador")))
    if num is None or den is None or abs(den) < 0.005:
        return None
    un = "R$" if (linha.get("unidade") or "") in ("R$", "%") else ""
    a, b = valor_com_unidade(num, un) if un else numero_br(num, 2), valor_com_unidade(den, un) if un else numero_br(den, 2)
    return f"{a} de {b} = {numero_br(100.0 * num / den, 1)}%"


def _f(v):
    try:
        return float(v) if v is not None and not isinstance(v, bool) else None
    except (TypeError, ValueError):
        return None


def periodo_br(p) -> str:
    s = str(p or "")
    return f"{s[5:7]}/{s[:4]}" if len(s) == 7 and s[4] == "-" else "—"


def avisos(linha: dict, interp: dict, historico: list | None = None) -> list:
    """Avisos simples de 'numero fora do comum' (nao e conclusao: e um convite para olhar). Regras: (1) valor mudou >= LIMITE_VARIACAO_PCT frente ao
    mes anterior gravado para a mesma empresa/obra/UN; (2) >= LIMITE_FAIXA_90_PCT do valor esta em faixa 'mais de 90 dias'."""
    saida = []
    atual, un, per = _f(linha.get("realizado")), linha.get("unidade"), str(linha.get("periodo") or "")
    if atual is not None and per:
        chave = (linha.get("empresa") or "", linha.get("obra") or "", linha.get("un") or "")
        ant = sorted((h for h in (historico or []) if str(h.get("periodo") or "") < per and _f(h.get("realizado")) is not None
                      and ((h.get("empresa") or "", h.get("obra") or "", h.get("un") or "") == chave)), key=lambda h: h["periodo"])
        if ant:
            prev = _f(ant[-1]["realizado"])
            if prev == 0 and atual != 0:
                saida.append(f"Em {periodo_br(ant[-1]['periodo'])} o valor era zero e agora é {valor_com_unidade(atual, un)}.")
            elif prev:
                var = 100.0 * (atual - prev) / abs(prev)
                if abs(var) >= LIMITE_VARIACAO_PCT:
                    saida.append(f"O valor mudou {'+' if var > 0 else '−'}{numero_br(abs(var), 1)}% frente a {periodo_br(ant[-1]['periodo'])} "
                                 f"({valor_com_unidade(prev, un)} → {valor_com_unidade(atual, un)}).")
    for t in interp.get("tabelas", []):
        for b in t["bruto"]:
            r = str(b.get("rotulo") or "").lower()
            if b.get("parte_pct") is not None and "90" in r and ("mais" in r or ">" in r) and b["parte_pct"] >= LIMITE_FAIXA_90_PCT:
                saida.append(f"{numero_br(b['parte_pct'], 1)}% do valor em «{t['titulo'].lower()}» está em «{b['rotulo']}».")
    return saida
