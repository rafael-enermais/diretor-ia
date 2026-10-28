# -*- coding: utf-8 -*-
import datetime as dt

import catalogo
import metricas_dados as md
import painel
import prontidao

ITENS = [
    {"item_id": "I01", "tipo": "indicador", "nome": "Receita", "categoria": "Resultado e margem", "responsavel": "Fulana de Tal", "app_origem": "GDF",
     "situacao": "Existe no app (conferir regra)", "referencia": "Budget", "fonte": "Sienge"},
    {"item_id": "I02", "tipo": "indicador", "nome": "Margem", "categoria": "Resultado e margem", "responsavel": "Fulana de Tal", "app_origem": "GDF",
     "situacao": "Parcial (calcular ou ligar)", "referencia": "Budget", "fonte": "Sienge"},
    {"item_id": "I22", "tipo": "indicador", "nome": "A receber", "categoria": "Recebíveis e pagáveis", "responsavel": "Beltrano Silva", "app_origem": "TIA.go",
     "situacao": "Falta construir", "referencia": "—", "fonte": "Planilha"},
    {"item_id": "E01", "tipo": "entrega", "nome": "Fechamento", "responsavel": "Fulana de Tal", "periodicidade": "Dia 7", "meta": "no prazo", "apuracao": "Checklist"},
    {"item_id": "E02", "tipo": "entrega", "nome": "Conciliação", "responsavel": "Beltrano Silva", "periodicidade": "Semanal", "meta": "100%", "apuracao": "Misto"},
]
ATUAIS = [
    {"item_id": "I01", "unidade": "R$", "periodo": "2026-09", "empresa": "", "obra": "", "un": "", "app_origem": "GDF", "meta": "100000", "previsto": None,
     "realizado": 90000, "pct_atingimento": 90, "status": "Atenção", "origem": "medido", "detalhe": "x", "atualizado_em": dt.datetime(2026, 10, 1, 12, 0, tzinfo=dt.timezone.utc)},
    {"item_id": "I22", "unidade": "R$", "periodo": "2026-09", "empresa": "A", "obra": "", "un": "", "app_origem": "GDF", "meta": None, "previsto": None,
     "realizado": 10, "pct_atingimento": None, "status": "No alvo", "origem": "medido", "detalhe": None, "atualizado_em": dt.datetime(2026, 10, 2, 12, 0, tzinfo=dt.timezone.utc)},
    {"item_id": "I22", "unidade": "R$", "periodo": "2026-09", "empresa": "B", "obra": "", "un": "", "app_origem": "GDF", "meta": None, "previsto": None,
     "realizado": 20, "pct_atingimento": None, "status": "Fora da meta", "origem": "manual", "detalhe": None, "atualizado_em": dt.datetime(2026, 10, 3, 12, 0, tzinfo=dt.timezone.utc)},
]


def test_status_do_item_pega_o_pior():
    assert md.status_do_item([]) == "Sem lançamento"
    assert md.status_do_item([{"status": "No alvo"}, {"status": "Fora da meta"}]) == "Fora da meta"
    assert md.status_do_item([{"status": "No alvo"}, {"status": "Atenção"}]) == "Atenção"
    assert md.status_do_item([{"status": "Sem lançamento"}, {"status": "No alvo"}]) == "No alvo"
    assert md.status_do_item([{"status": "Sem lançamento"}]) == "Sem lançamento"
    assert md.status_do_item([{"status": "lixo"}]) == "Sem lançamento"


def test_periodo_e_datas():
    assert md.periodo_br("2026-09") == "09/2026" and md.periodo_br(None) == "—" and md.periodo_br("xx") == "—"
    por = md.agrupar_por_item(ATUAIS)
    assert md.periodo_recente(por["I22"]) == "2026-09"
    assert md.ultima_atualizacao(por["I22"]).day == 3
    assert md.contar_status(["No alvo", "No alvo", "?"]) == {"Fora da meta": 0, "Atenção": 0, "No alvo": 2, "Sem lançamento": 1}


def test_catalogo_categorias():
    assert catalogo.categorias_em_ordem(ITENS) == ["Resultado e margem", "Recebíveis e pagáveis"]
    assert [len(v) for v in catalogo.por_categoria(ITENS).values()] == [2, 1]
    assert len(catalogo.indicadores(ITENS)) == 3 and len(catalogo.entregas(ITENS)) == 2


def test_tabela_indicadores_nao_recalcula_e_mostra_so_primeiro_nome():
    por = md.agrupar_por_item(ATUAIS)
    t = painel.tabela_indicadores(ITENS, por)
    i01, i02, i22 = t
    assert i01["Valor"] == "R$ 90.000,00" and i01["Meta"] == "R$ 100.000,00" and i01["% da meta"] == "90,0%" and i01["Status"] == "🟡 Atenção"
    assert i01["Responsável"] == "Fulana" and i22["Responsável"] == "Beltrano"
    assert i02["Valor"] == "—" and i02["Status"] == "⚪ Sem lançamento" and i02["Período"] == "—"
    assert i22["Valor"].startswith("2 linhas") and i22["Status"] == "🔴 Fora da meta"          # varias linhas: nao soma
    assert [r["ID"] for r in painel.tabela_indicadores(ITENS, por, "Recebíveis e pagáveis")] == ["I22"]


def test_resumos():
    por = md.agrupar_por_item(ATUAIS)
    r = painel.resumo_geral(ITENS, por)
    assert r["indicadores"] == 3 and r["entregas"] == 2 and r["ind_com_valor"] == 2 and r["ent_com_valor"] == 0
    assert r["status_indicadores"]["Fora da meta"] == 1 and r["status_indicadores"]["Sem lançamento"] == 1
    cats = painel.resumo_por_categoria(ITENS, por)
    assert cats[0]["Categoria"] == "Resultado e margem" and cats[0]["Indicadores"] == 2 and cats[0]["Com valor"] == 1
    ent = painel.tabela_entregas(ITENS, por)
    assert ent[0]["Responsável"] == "Fulana" and ent[0]["Status"] == "⚪ Sem lançamento" and ent[0]["Prazo"] == "Dia 7"
    assert len(painel.linhas_detalhe(por["I22"])) == 2


def test_prontidao():
    por = md.agrupar_por_item(ATUAIS)
    assert prontidao.situacao_chave("Existe no app (conferir regra)") == "Existe no app"
    assert prontidao.situacao_chave("Input manual") == "Input manual" and prontidao.situacao_chave(None) == "Sem definição"
    ps = {r["Situação"]: r for r in prontidao.por_situacao(ITENS, por)}
    assert ps["Existe no app"]["Já recebendo dado"] == 1 and ps["Parcial"]["Já recebendo dado"] == 0 and ps["Falta construir"]["Já recebendo dado"] == 1
    assert {r["App / sistema"] for r in prontidao.por_fonte(ITENS, por)} == {"GDF", "TIA.go"}
    assert [r["ID"] for r in prontidao.sem_dado_ainda(ITENS, por)] == ["I02"]
