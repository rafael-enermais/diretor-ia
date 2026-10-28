# -*- coding: utf-8 -*-
"""Formatos brasileiros para a tela (puro, sem Streamlit)."""
from __future__ import annotations

from decimal import Decimal

STATUS_ICONE = {"No alvo": "🟢", "Atenção": "🟡", "Fora da meta": "🔴", "Sem meta": "🔵", "Sem lançamento": "⚪"}
STATUS_SEM = "Sem lançamento"


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def numero_br(v, casas: int = 2) -> str:
    n = _num(v)
    if n is None:
        return "—"
    s = f"{n:,.{casas}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def valor_com_unidade(v, unidade: str | None) -> str:
    """12345.6 + 'R$' -> 'R$ 12.345,60'; 12.5 + '%' -> '12,5%'; 3 + 'dias' -> '3 dias'. Vazio -> '—'. Texto que nao e numero volta como esta."""
    n = _num(v)
    if n is None:
        return "—" if v in (None, "") else str(v)
    u = (unidade or "").strip()
    if u == "R$":
        return ("-" if n < 0 else "") + "R$ " + numero_br(abs(n), 2)
    if u == "%":
        return numero_br(n, 1) + "%"
    if u in ("dias", "dia"):
        return numero_br(n, 0) + (" dia" if abs(n) == 1 else " dias")
    if u in ("un", ""):
        return numero_br(n, 0 if n == int(n) else 2)
    return numero_br(n, 2) + " " + u


def pct_br(v) -> str:
    n = _num(v)
    return "—" if n is None else numero_br(n, 1) + "%"


def status_ou_sem(status) -> str:
    return status if status in STATUS_ICONE else STATUS_SEM


def status_com_icone(status) -> str:
    s = status_ou_sem(status)
    return f"{STATUS_ICONE[s]} {s}"


def primeiro_nome(texto) -> str:
    t = (texto or "").strip()
    return t.split()[0] if t else "—"


def primeiros_nomes(texto) -> str:
    """'Fulana de Tal / Beltrano Silva' -> 'Fulana / Beltrano' (so o primeiro nome de cada pessoa; decisao do responsavel pelo painel). Vazio -> '—'."""
    import re
    partes = [p.strip() for p in re.split(r"\s*(?:/|,|;|\+|\be\b)\s*", str(texto or "")) if p.strip()]
    return " / ".join(primeiro_nome(p) for p in partes) if partes else "—"
