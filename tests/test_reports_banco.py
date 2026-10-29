# -*- coding: utf-8 -*-
import datetime as dt

import chat_ferramentas as FERR
import reports
from banco import Banco
from fakes import BancoFalso

HOJE = dt.date(2026, 10, 29)


def _item(id_, colab="Fulana Silva", semana=dt.date(2026, 10, 26), tipo="dificuldade", urg="media", sit="nova", recebido=dt.datetime(2026, 10, 27, 9), resolvido=None, titulo="t"):
    return {"id": id_, "origem": "manual", "id_externo": None, "colaborador": colab, "semana_de": semana, "tipo": tipo, "urgencia": urg, "situacao": sit, "titulo": titulo,
            "descricao": "d", "nota_diretor": None, "recebido_em": recebido, "resolvido_em": resolvido, "criado_por": "u", "atualizado_em": recebido, "atualizado_por": None,
            "vinculo_item_id": None, "vinculo_recusados": None}


def test_segunda_da_semana():
    assert reports.segunda_da_semana(dt.date(2026, 10, 28)) == dt.date(2026, 10, 26)      # quarta -> segunda
    assert reports.segunda_da_semana(dt.date(2026, 10, 26)) == dt.date(2026, 10, 26)


def test_instalado_so_com_as_duas_tabelas():
    assert reports.instalado(BancoFalso([[{"a": True, "b": True, "c": True}]])) is True
    assert reports.instalado(BancoFalso([[{"a": True, "b": False, "c": True}]])) is False
    assert reports.instalado(BancoFalso([[{"a": True, "b": True, "c": False}]])) is False           # SQL-05 (colunas de vinculo) ainda nao rodado
    assert reports.instalado(BancoFalso([[]])) is False
    assert reports.instalado(BancoFalso(falhar=True)) is False                              # erro de banco: a tela explica, nao quebra


def test_validar_nao_bloqueia_e_avisa():
    d, av = reports.validar({"colaborador": "  Fulano  ", "semana_de": dt.date(2026, 10, 29), "tipo": "problema", "urgencia": "alta", "situacao": "acompanhamento",
                             "titulo": "ok\x00", "descricao": "", "nota_diretor": None}, HOJE)
    assert not av and d["colaborador"] == "Fulano" and d["semana_de"] == dt.date(2026, 10, 26) and d["titulo"] == "ok" and d["descricao"] is None
    assert (d["tipo"], d["urgencia"], d["situacao"]) == ("problema", "alta", "acompanhamento")
    # tudo em branco/estranho: salva do mesmo jeito, com padroes e avisos em linguagem simples
    d, av = reports.validar({"colaborador": "x", "semana_de": None, "tipo": "?", "urgencia": "?", "situacao": "?"}, HOJE)
    assert len(av) == 2 and d["colaborador"] == reports.SEM_NOME and d["semana_de"] == dt.date(2026, 10, 26)
    assert (d["tipo"], d["urgencia"], d["situacao"]) == ("dificuldade", "media", "nova")
    d, av = reports.validar({}, dt.date(2026, 10, 28))
    assert d["colaborador"] == reports.SEM_NOME and d["titulo"] is None and d["nota_diretor"] is None
    d, av = reports.validar({"colaborador": "Fulano", "semana_de": dt.date(2026, 10, 26), "titulo": "a" * 500, "descricao": "a" * 5000})
    assert not av and len(d["titulo"]) == 200 and len(d["descricao"]) == 4000


def test_criar_item_e_historico_num_comando_so():
    dados, _ = reports.validar({"colaborador": "Fulana", "semana_de": dt.date(2026, 10, 26), "situacao": "resolvida"}, HOJE)
    b = BancoFalso()
    reports.criar(b, "u@x.com", dados)
    sql, params = b.comandos[0]
    assert len(b.comandos) == 1 and sql.lstrip().upper().startswith("WITH") and "report_item_historico" in sql and "DELETE" not in sql.upper()
    assert "Fulana" in params and "u@x.com" in params and "resolvida" in params


def test_diferencas_ignora_vazio_igual_none():
    a = _item(1)
    a["nota_diretor"] = None
    novo = {c: a[c] for c in reports.CAMPOS}
    assert reports.diferencas(a, novo) == []
    novo["nota_diretor"] = "   "                                                        # espacos = vazio = None: nao e' mudanca
    assert reports.diferencas(a, novo) == []
    novo["urgencia"], novo["nota_diretor"] = "alta", "ligar hoje"
    assert [c for c, _, _ in reports.diferencas(a, novo)] == ["urgencia", "nota_diretor"]


def test_atualizar_grava_so_o_que_mudou_com_historico_e_sem_delete():
    a = _item(5)
    novo = {c: a[c] for c in reports.CAMPOS}
    b = BancoFalso()
    assert reports.atualizar(b, "u@x.com", 5, a, novo) == 0 and not b.transacoes         # nada mudou: nao grava nada
    novo.update(urgencia="critica", situacao="resolvida")
    assert reports.atualizar(b, "u@x.com", 5, a, novo) == 2
    tx = b.transacoes[0]
    assert [c[0].lstrip().split()[0].upper() for c in tx] == ["UPDATE", "INSERT", "INSERT"]       # tudo na MESMA transacao
    upd = tx[0][0]
    assert "urgencia = %s" in upd and "situacao = %s" in upd and "titulo" not in upd and "resolvido_em = COALESCE(resolvido_em, now())" in upd
    assert tx[0][1][-1] == 5 and tx[1][1][2] == "urgencia" and tx[1][1][3:] == ("Média", "Crítica")
    assert "DELETE" not in " ".join(c[0].upper() for c in tx)
    # reabrir limpa a data de resolucao
    b2 = BancoFalso()
    res = _item(6, sit="resolvida", resolvido=dt.datetime(2026, 10, 28))
    nv = {c: res[c] for c in reports.CAMPOS}
    nv["situacao"] = "acompanhamento"
    reports.atualizar(b2, "u@x.com", 6, res, nv)
    assert "resolvido_em = NULL" in b2.transacoes[0][0][0]
    # mudar so a nota nao mexe na data de resolucao
    b3 = BancoFalso()
    nv2 = {c: res[c] for c in reports.CAMPOS}
    nv2["nota_diretor"] = "ok"
    reports.atualizar(b3, "u@x.com", 6, res, nv2)
    assert "resolvido_em" not in b3.transacoes[0][0][0]


def test_kpis_e_series():
    itens = [
        _item(1, "Fulana Silva", urg="critica"), _item(2, "Fulana Silva", urg="alta", sit="acompanhamento"), _item(3, "Beto Souza", urg="baixa"),
        _item(4, "Beto Souza", sit="resolvida", recebido=dt.datetime(2026, 10, 20), resolvido=dt.datetime(2026, 10, 24)),
        _item(5, "Ciro Lima", sit="arquivada", urg="critica"),
        _item(6, "Ciro Lima", sit="resolvida", recebido=dt.datetime(2026, 8, 1), resolvido=dt.datetime(2026, 8, 3)),
    ]
    k = reports.kpis(itens, HOJE)
    assert (k["abertas"], k["urgentes"], k["criticas"], k["resolvidas_30d"], k["colaboradores_com_aberta"]) == (3, 2, 1, 1, 2)
    assert k["dias_medios_para_resolver"] == 3.0                                          # (4 + 2) / 2
    assert reports.kpis([], HOJE)["dias_medios_para_resolver"] is None
    ab = reports.abertas_por_colaborador(itens)
    assert list(ab.index) == ["Fulana Silva", "Beto Souza"] and list(ab.columns) == ["Baixa", "Média", "Alta", "Crítica"]
    assert ab.loc["Fulana Silva", "Crítica"] == 1 and ab.loc["Beto Souza", "Baixa"] == 1
    assert reports.abertas_por_colaborador([_item(1, sit="resolvida")]).empty
    ss = reports.serie_semanal(itens)
    assert ss.loc["26/10/2026", "Dificuldade"] == 6
    nr = reports.novos_x_resolvidos(itens)
    assert nr.loc["26/10/2026", "Novos"] == 6 and nr.loc["19/10/2026", "Resolvidos"] == 1 and nr.loc["03/08/2026", "Resolvidos"] == 1
    assert reports.serie_semanal([]).empty and reports.novos_x_resolvidos([]).empty


def test_ferramenta_pendencias_do_chat():
    itens = [_item(1, "Fulana Silva", urg="critica", titulo="Sem acesso ao ERP"), _item(2, "Beto Souza", urg="baixa"),
             _item(3, "Ciro Lima", sit="resolvida", resolvido=dt.datetime(2026, 10, 28)), _item(4, reports.SEM_NOME, urg="alta")]
    ctx = FERR.Contexto(BancoFalso([[{"a": True, "b": True, "c": True}], itens]), [], {})
    r, tab = FERR.executar(ctx, "pendencias", {})
    assert r["encontrados"] == 3 and r["itens"][0]["urgencia"] == "Crítica" and r["itens"][0]["colaborador"] == "Fulana"      # so' primeiro nome; mais urgente primeiro
    assert r["itens"][1]["colaborador"] == reports.SEM_NOME and r["resumo_geral"]["em_aberto"] == 3 and tab
    ctx = FERR.Contexto(BancoFalso([[{"a": True, "b": True, "c": True}], itens]), [], {})
    r, _ = FERR.executar(ctx, "pendencias", {"situacao": "resolvida", "colaborador": "ciro"})
    assert r["encontrados"] == 1 and r["itens"][0]["colaborador"] == "Ciro"
    # SQL-04 ainda nao rodado: resposta clara, sem quebrar
    r, _ = FERR.executar(FERR.Contexto(BancoFalso([[{"a": False, "b": False, "c": False}]]), [], {}), "pendencias", {})
    assert "SQL-04" in r["aviso"] and "SQL-05" in r["aviso"]


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
