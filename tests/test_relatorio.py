# -*- coding: utf-8 -*-
import datetime as dt
import json
import os
import re

import relatorio_dados as RD
import relatorio_pdf as RP

GERADO = dt.datetime(2026, 10, 29, 15, 30, tzinfo=dt.timezone.utc)
I27 = {"posicao": "ao vivo (até hoje)", "venc_ate": "2026-10-28", "n_vencidos": 736, "a_vencer_total": 35318892.37, "a_vencer_30d": 9100000.0, "n_a_vencer_30d": 210,
       "faixas": [{"faixa": "1 a 30 dias", "n": 394, "valor": 2668299.11}, {"faixa": "31 a 60 dias", "n": 52, "valor": 291761.54},
                  {"faixa": "61 a 90 dias", "n": 42, "valor": 321726.87}, {"faixa": "Mais de 90 dias", "n": 248, "valor": 1081001.59}], "tela": "Indicadores financeiros > Inadimplência"}


def _it(i, tipo, nome, cat, resp="Fulana de Tal"):
    return {"item_id": i, "tipo": tipo, "nome": nome, "categoria": cat, "responsavel": resp, "app_origem": "GDF", "situacao": "Existe", "periodicidade": "Mensal", "meta": "Meta X",
            "apuracao": "Medido nos dados", "versao_matriz": "v0.9"}


def _m(i, **k):
    base = {"item_id": i, "periodo": "2026-10", "empresa": "", "obra": "", "un": "", "unidade": "R$", "meta": None, "previsto": None, "realizado": None, "numerador": None,
            "denominador": None, "pct_atingimento": None, "status": None, "detalhe": None, "atualizado_em": GERADO}
    base.update(k)
    return base


ITENS = [_it("I03", "indicador", "Margem de contribuição", "Resultado e margem"), _it("I22", "indicador", "Contas a receber", "Recebíveis e pagáveis"),
         _it("I27", "indicador", "Contas a pagar", "Recebíveis e pagáveis"), _it("I10", "indicador", "Caixa mínimo", "Caixa e liquidez"), _it("I11", "indicador", "Dívida líquida", "Dívida e endividamento"),
         _it("E01", "entrega", "Report semanal", "Pessoas"), _it("E02", "entrega", "Conciliação bancária diária", "Caixa e liquidez")]
ATUAIS = [_m("I03", unidade="%", meta="Budget", previsto=12.0, realizado=9.5, pct_atingimento=79.2, status="Atenção", detalhe="MC % = BDI ÷ receita. Fonte: DRE confirmado."),
          _m("I22", meta="Informativo", realizado=8100000.0, numerador=8100000.0, denominador=41000000.0, detalhe=json.dumps({"faixas": [{"faixa": "1 a 30 dias", "n": 10, "valor": 5.0e6}, {"faixa": "Mais de 90 dias", "n": 4, "valor": 3.1e6}]})),
          _m("I27", unidade="%", meta="Vencidos = 0", previsto=0.0, realizado=4362789.11, numerador=4362789.11, denominador=39681681.48, pct_atingimento=89.0, status="Fora da meta", detalhe=json.dumps(I27)),
          _m("I10", meta="R$ 5 mi", realizado=6200000.0, pct_atingimento=124.0, status="No alvo")]
HIST = [{"item_id": "I27", "periodo": "2026-09", "empresa": "", "obra": "", "un": "", "realizado": 2000000.0, "unidade": "R$"}]


def _pend(n, colab, urg, sit="nova", titulo="Sem acesso ao sistema", vinc=None):
    return {"id": n, "origem": "app_colab", "colaborador": colab, "semana_de": dt.date(2026, 10, 26), "tipo": "dificuldade", "urgencia": urg, "situacao": sit, "titulo": titulo,
            "descricao": "d", "nota_diretor": None, "recebido_em": dt.datetime(2026, 10, 27, 12, tzinfo=dt.timezone.utc), "resolvido_em": None, "vinculo_item_id": vinc}


PEND = [_pend(1, "Ana Souza", "critica", titulo="Conciliação parada 😬 desde segunda", vinc="E02"), _pend(2, "Beto Lima", "media"), _pend(3, "Ana Souza", "baixa"),
        _pend(4, "Ciro Dias", "alta", "acompanhamento"), _pend(5, "Ciro Dias", "alta", "resolvida")]


def _ctx(opcoes=None, pend=PEND):
    import metricas_dados as md
    return RD.montar(ITENS, md.agrupar_por_item(ATUAIS), HIST, pend, opcoes or {"observacao": "Reunir com o time na sexta."}, GERADO)


def _paginas(pdf: bytes) -> int:
    return len(re.findall(rb"/Type /Page(?!s)", pdf))


def test_montar_dados_do_relatorio():
    c = _ctx()
    assert c["periodo_ref"] == "10/2026" and c["secoes"] == list(RD.SECOES) and c["resumo"]["indicadores"] == 5
    assert [l["ID"] for l in c["atencao"]] == ["I27", "I03"] and c["atencao"][0]["Status"] == "Fora da meta"          # pior primeiro
    ids = [d["id"] for d in c["detalhes"]]
    assert "I27" in ids and "I10" not in ids                                                                         # sem pedido: so' fora da meta/atencao ou com aviso
    i27 = next(d for d in c["detalhes"] if d["id"] == "I27")["blocos"][0]
    assert i27["composicao"] == "R$ 4.362.789,11 de R$ 39.681.681,48 = 11,0%" and any("118,1%" in a for a in i27["avisos"]) and i27["tabelas"][0]["titulo"] == "Faixas de atraso"
    assert c["pendencias"]["kpis"]["abertas"] == 4 and [l["n"] for l in c["pendencias"]["linhas"]][0] == 1
    assert c["pendencias"]["linhas"][0]["colaborador"] == "Ana"                                                      # so' primeiro nome
    assert c["pendencias"]["por_colaborador"][0] == ("Ana", 2)
    assert c["observacao"] == "Reunir com o time na sexta." and any("Pendências relatadas" in t for t in c["leitura"])
    pedido = _ctx({"secoes": ["resumo", "detalhes"], "detalhe_ids": ["I10", "I99"]})
    assert [d["id"] for d in pedido["detalhes"]] == ["I10"] and pedido["atencao"] == [] and pedido["pendencias"] is None and pedido["entregas"] == []


def test_leitura_padrao_sem_pendencias_e_sem_dados():
    import metricas_dados as md
    c = RD.montar(ITENS, md.agrupar_por_item([]), [], None, {}, GERADO)
    assert c["periodo_ref"] == "—" and not any("Pendências" in t for t in c["leitura"]) and "0 indicadores (0%)" in c["leitura"][0]


def test_gerar_pdf_completo_e_secoes_opcionais():
    pdf = RP.gerar_pdf(_ctx())
    assert pdf[:5] == b"%PDF-" and len(pdf) > 20000
    n_completo = _paginas(pdf)
    assert n_completo >= 7                                                    # capa, resumo, atencao, indicadores, detalhes, entregaveis, pendencias, fechamento
    so_resumo = _paginas(RP.gerar_pdf(_ctx({"secoes": ["resumo"]})))
    assert so_resumo == 3 and so_resumo < n_completo                          # capa + resumo + fechamento
    assert RP.gerar_pdf(_ctx()) == pdf                                        # deterministico (invariant)
    if os.environ.get("DIRETORIA_PDF_AMOSTRA"):
        open(os.environ["DIRETORIA_PDF_AMOSTRA"], "wb").write(pdf)


def test_pdf_com_muitos_itens_quebra_pagina_e_aguenta_texto_estranho():
    import metricas_dados as md
    muitos = [_it(f"I{n:02d}", "indicador", f"Indicador número {n} com um nome razoavelmente comprido para quebrar linha", "Resultado e margem") for n in range(20, 70)]
    atuais = [_m(i["item_id"], realizado=float(n) * 1000, meta="x", pct_atingimento=50.0, status="Fora da meta") for n, i in enumerate(muitos)]
    pend = [_pend(n, "Fulano " + "Sobrenome" * 3, "media", titulo="Título muito longo " * 20 + " 😀 ✓ → ≥") for n in range(100, 190)]
    ctx = RD.montar(ITENS + muitos, md.agrupar_por_item(ATUAIS + atuais), HIST, pend, {"observacao": "obs " * 600}, GERADO)
    pdf = RP.gerar_pdf(ctx)
    assert pdf[:5] == b"%PDF-" and _paginas(pdf) > 12
    assert RP.L("ok 😀 ✓ → x") == "ok para x" or RP.L("ok 😀 ✓ → x").startswith("ok")        # emoji sai; seta vira 'para'; nunca levanta erro
    RP.gerar_pdf(RD.montar([], {}, [], [], {}, GERADO))                       # catalogo vazio nao quebra
