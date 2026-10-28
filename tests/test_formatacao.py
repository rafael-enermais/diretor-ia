# -*- coding: utf-8 -*-
import datetime as dt
from decimal import Decimal

import formatacao as f
from fuso import fmt_br
from texto import limpar_texto


def test_numero_br():
    assert f.numero_br(1234567.891) == "1.234.567,89"
    assert f.numero_br(None) == "—"
    assert f.numero_br(Decimal("10.5"), 1) == "10,5"


def test_valor_com_unidade():
    assert f.valor_com_unidade(12345.6, "R$") == "R$ 12.345,60"
    assert f.valor_com_unidade(-5, "R$") == "-R$ 5,00"
    assert f.valor_com_unidade(12.55, "%") == "12,6%" or f.valor_com_unidade(12.55, "%") == "12,5%"
    assert f.valor_com_unidade(1, "dias") == "1 dia"
    assert f.valor_com_unidade(3, "dias") == "3 dias"
    assert f.valor_com_unidade(None, "R$") == "—"
    assert f.valor_com_unidade("texto livre", "R$") == "texto livre"
    assert f.valor_com_unidade(True, "R$") != "R$ 1,00"          # booleano nao vira numero


def test_status():
    assert f.status_com_icone("No alvo") == "🟢 No alvo"
    assert f.status_com_icone("coisa estranha") == "⚪ Sem lançamento"
    assert f.status_ou_sem(None) == "Sem lançamento"


def test_primeiros_nomes():
    assert f.primeiro_nome("Fulana de Tal") == "Fulana"
    assert f.primeiros_nomes("Fulana de Tal / Beltrano Silva") == "Fulana / Beltrano"
    assert f.primeiros_nomes("Ana e Bruno Dias") == "Ana / Bruno"
    assert f.primeiros_nomes(None) == "—"


def test_fmt_br():
    assert fmt_br(None) == "—"
    assert fmt_br(dt.date(2026, 10, 28)) == "28/10/2026"
    assert fmt_br(dt.datetime(2026, 10, 28, 15, 0, tzinfo=dt.timezone.utc)) == "28/10/2026 12:00"    # UTC-3


def test_limpar_texto():
    assert limpar_texto("  oi\x00 mundo  ") == "oi mundo"
    assert limpar_texto("a​b‮c") == "abc"                  # invisiveis saem
    assert limpar_texto("abcdef", 3) == "abc"
    assert limpar_texto(None) == ""
