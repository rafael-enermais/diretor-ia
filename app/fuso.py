# -*- coding: utf-8 -*-
"""Horario de Brasilia (o banco guarda em UTC; a tela sempre mostra o horario de Sao Paulo)."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

BR = ZoneInfo("America/Sao_Paulo")


def agora_br() -> dt.datetime:
    return dt.datetime.now(BR)


def fmt_br(valor) -> str:
    """datetime/date -> 'dd/mm/aaaa HH:MM' (hora de Brasilia). Vazio -> '—'. Texto nao reconhecido volta como esta."""
    if valor is None or valor == "":
        return "—"
    if isinstance(valor, dt.datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=dt.timezone.utc)
        return valor.astimezone(BR).strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, dt.date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)
