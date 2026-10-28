# -*- coding: utf-8 -*-
"""Diretor.IA - tendencia simples de uma serie mensal (minimos quadrados). Puro. NAO e previsao oficial: e' a reta que melhor se ajusta aos meses ja gravados
pelos apps de origem; so' existe com 3 ou mais meses e sempre vem com o aviso. Serve para o Diretor ver para onde o numero caminha, nao para decidir sozinho."""
from __future__ import annotations

MIN_MESES = 3
AVISO = "Tendência linear simples sobre os meses já gravados; não é previsão oficial e não considera sazonalidade, orçamento nem fatos novos."


def _indice(periodo: str) -> int:
    return int(periodo[:4]) * 12 + int(periodo[5:7]) - 1


def _periodo(indice: int) -> str:
    return f"{indice // 12:04d}-{indice % 12 + 1:02d}"


def tendencia(pontos, horizonte: int = 3) -> dict:
    """pontos = [(periodo 'AAAA-MM', valor numerico)] (qualquer ordem). Devolve {'ok': bool, ...}."""
    limpos = {}
    for p, v in pontos or []:
        try:
            if isinstance(v, bool) or v is None or len(str(p)) != 7:
                continue
            limpos[_indice(str(p))] = float(v)
        except (TypeError, ValueError):
            continue
    xs = sorted(limpos)
    if len(xs) < MIN_MESES:
        return {"ok": False, "meses": len(xs), "motivo": f"São necessários pelo menos {MIN_MESES} meses gravados (há {len(xs)})."}
    ys = [limpos[x] for x in xs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    inclinacao = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercepto = my - inclinacao * mx
    proximos = [(_periodo(xs[-1] + k), round(intercepto + inclinacao * (xs[-1] + k), 2)) for k in range(1, max(1, min(int(horizonte), 6)) + 1)]
    ultimo, anterior = ys[-1], ys[-2]
    var = None if anterior == 0 else round((ultimo - anterior) / abs(anterior) * 100, 1)
    return {"ok": True, "meses": n, "inclinacao_por_mes": round(inclinacao, 2), "variacao_ultimo_mes_pct": var,
            "direcao": "subindo" if inclinacao > 0 else "caindo" if inclinacao < 0 else "estável", "proximos": proximos, "aviso": AVISO}
