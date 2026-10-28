# -*- coding: utf-8 -*-
"""Higiene de texto digitado na tela: tira caracteres de controle e Unicode invisivel (usado para esconder ordens em texto), limita o tamanho."""
from __future__ import annotations

import re
import unicodedata

_CONTROLE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SEM_FORMA = {0x115F, 0x1160, 0x17B4, 0x17B5, 0x2800, 0x3164, 0xFFA0}


def _escondido(ch: str) -> bool:
    o = ord(ch)
    if o < 0x80:
        return False
    if o in _SEM_FORMA or 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF:
        return True
    return unicodedata.category(ch) in ("Cf", "Co", "Cn", "Cs")


def limpar_texto(s, maximo: int | None = None) -> str:
    t = _CONTROLE.sub("", str(s if s is not None else ""))
    if not t.isascii():
        t = "".join(c for c in t if not _escondido(c))
    t = t.strip()
    return t[:maximo] if maximo else t
