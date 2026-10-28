# -*- coding: utf-8 -*-
"""Coloca app/ no caminho de importacao (o app roda com app/ como pasta-raiz dos modulos)."""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
for p in (RAIZ / "app", RAIZ / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
