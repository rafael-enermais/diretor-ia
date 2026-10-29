# -*- coding: utf-8 -*-
import datetime as dt

import reports
from banco import Banco
from fakes import BancoFalso


def test_segunda_da_semana():
    assert reports.segunda_da_semana(dt.date(2026, 10, 28)) == dt.date(2026, 10, 26)      # quarta -> segunda
    assert reports.segunda_da_semana(dt.date(2026, 10, 26)) == dt.date(2026, 10, 26)


def test_validar_nao_bloqueia_e_avisa():
    d, av = reports.validar({"semana_de": dt.date(2026, 10, 29), "de_quem": "  Fulano  ", "resumo": "ok\x00", "dificuldades": "", "recebido_em": None, "status": "tratado"})
    assert not av and d["semana_de"] == dt.date(2026, 10, 26) and d["de_quem"] == "Fulano" and d["resumo"] == "ok" and d["dificuldades"] is None
    # tudo em branco/estranho: salva do mesmo jeito, com valores padrao e avisos em linguagem simples
    d, av = reports.validar({"semana_de": None, "de_quem": "x", "status": "?"}, dt.date(2026, 10, 29))
    assert len(av) == 2 and d["de_quem"] == reports.SEM_NOME and d["semana_de"] == dt.date(2026, 10, 26) and d["status"] == "recebido"
    d, av = reports.validar({}, dt.date(2026, 10, 28))
    assert d["de_quem"] == reports.SEM_NOME and d["resumo"] is None and d["recebido_em"] is None
    d, av = reports.validar({"semana_de": dt.date(2026, 10, 26), "de_quem": "Fulano", "resumo": "a" * 5000})
    assert not av and len(d["resumo"]) == 4000


def test_criar_revisar_arquivar_restaurar_sem_delete():
    dados, _ = reports.validar({"semana_de": dt.date(2026, 10, 26), "de_quem": "Fulano"})
    b = BancoFalso()
    reports.criar(b, "u@x.com", dados)
    assert b.comandos[0][0].lstrip().upper().startswith("INSERT")
    reports.revisar(b, "u@x.com", 7, dados, "corrigi a semana")
    tx = b.transacoes[0]
    assert [c[0].lstrip().split()[0].upper() for c in tx] == ["INSERT", "UPDATE"]        # na MESMA transacao; nenhum DELETE
    assert tx[0][1][-1] == 7 and tx[1][1][-1] == 7 and tx[1][1][1] == "corrigi a semana"
    reports.revisar(b, "u@x.com", 8, dados)                                              # motivo e' opcional
    assert b.transacoes[1][1][1][1] == "Editado"
    reports.arquivar(b, "u@x.com", 9)
    reports.restaurar(b, "u@x.com", 9)
    cmds = [c[0].lstrip().split()[0].upper() for c in b.comandos]
    assert cmds[-2:] == ["UPDATE", "UPDATE"] and "DELETE" not in " ".join(c[0].upper() for c in b.comandos)


class _Cur:
    def __init__(self, conn):
        self.conn, self.description = conn, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.conn.log.append(sql)
        if "FALHA" in sql:
            raise RuntimeError("falhou")
        if sql.startswith("SELECT"):
            self.description = [("a",), ("b",)]

    def fetchall(self):
        return [(1, 2)]


class _Conn:
    def __init__(self):
        self.log, self.autocommit, self.closed = [], True, 0

    def cursor(self):
        return _Cur(self)

    def commit(self):
        self.log.append("COMMIT")

    def rollback(self):
        self.log.append("ROLLBACK")


def test_banco_consultar_devolve_dicts():
    assert Banco(_Conn()).consultar("SELECT a, b") == [{"a": 1, "b": 2}]


def test_banco_transacao_commit_e_rollback():
    c = _Conn()
    b = Banco(c)
    b.executar_varios([("INSERT 1", None), ("UPDATE 2", None)])
    assert c.log[-1] == "COMMIT" and c.autocommit is True
    c2 = _Conn()
    try:
        Banco(c2).executar_varios([("INSERT 1", None), ("FALHA", None)])
    except RuntimeError:
        pass
    else:
        raise AssertionError("deveria subir o erro")
    assert c2.log[-1] == "ROLLBACK" and "COMMIT" not in c2.log and c2.autocommit is True
