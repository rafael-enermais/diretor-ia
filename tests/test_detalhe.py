# -*- coding: utf-8 -*-
import json

import detalhe as D

I27 = {"posicao": "ao vivo (até hoje)", "venc_ate": "2026-10-28", "n_vencidos": 736, "a_vencer_total": 35318892.37, "a_vencer_30d": 9100000.0, "n_a_vencer_30d": 210,
       "faixas": [{"faixa": "1 a 30 dias", "n": 394, "valor": 2668299.11}, {"faixa": "31 a 60 dias", "n": 52, "valor": 291761.54},
                  {"faixa": "61 a 90 dias", "n": 42, "valor": 321726.87}, {"faixa": "Mais de 90 dias", "n": 248, "valor": 1081001.59}],
       "tela": "Indicadores financeiros > Inadimplência"}
LINHA = {"item_id": "I27", "periodo": "2026-10", "unidade": "%", "realizado": 4362789.11, "numerador": 4362789.11, "denominador": 39681681.48, "empresa": "", "obra": "", "un": ""}


def test_carregar_json_texto_e_vazio():
    assert D.carregar(None) == (None, None) and D.carregar("") == (None, None)
    assert D.carregar('{"a": 1}') == ({"a": 1}, None)
    assert D.carregar({"a": 1}) == ({"a": 1}, None)
    est, txt = D.carregar("MC % = BDI ÷ receita. Fonte: DRE.")
    assert est is None and txt.startswith("MC %")
    assert D.carregar("{quebrado")[1] == "{quebrado"                  # JSON invalido nao derruba: vira texto


def test_formatacao_pela_chave():
    assert D.formatar("n_vencidos", 736) == "736"
    assert D.formatar("a_vencer_total", 35318892.37) == "R$ 35.318.892,37"
    assert D.formatar("prazo_medio_dias", 47.4) == "47 dias"
    assert D.formatar("venc_ate", "2026-10-28") == "28/10/2026"
    assert D.formatar("margem_pct", 11.04) == "11,0%"
    assert D.formatar("x", None) == "—" and D.formatar("flag", True) == "Sim"
    assert D.rotulo("faixas") == "Faixas de atraso" and D.rotulo("alguma_coisa_nova") == "Alguma coisa nova"


def test_interpretar_i27_campos_e_tabela_com_percentual():
    r = D.interpretar(json.dumps(I27))
    campos = dict(r["campos"])
    assert campos["Títulos vencidos"] == "736" and campos["A vencer (total)"] == "R$ 35.318.892,37" and campos["Vencidos até"] == "28/10/2026"
    assert campos["Títulos a vencer em 30 dias"] == "210"
    assert len(r["tabelas"]) == 1
    t = r["tabelas"][0]
    assert t["titulo"] == "Faixas de atraso" and len(t["linhas"]) == 4
    primeira = t["linhas"][0]
    assert primeira["Faixa de atraso"] == "1 a 30 dias" and primeira["Títulos"] == "394" and primeira["Valor"] == "R$ 2.668.299,11"
    assert primeira["% do total"] == "61,2%" and t["linhas"][3]["% do total"] == "24,8%"
    assert round(sum(b["parte_pct"] for b in t["bruto"])) == 100


def test_interpretar_texto_simples_e_lista_solta():
    r = D.interpretar("Fonte: DRE confirmado. Tela: Painel.")
    assert r["texto"].startswith("Fonte") and not r["campos"] and not r["tabelas"]
    r = D.interpretar([{"obra": "A", "valor": 10.0}, {"obra": "B", "valor": 30.0}])
    assert r["tabelas"][0]["linhas"][1]["% do total"] == "75,0%"
    assert D.interpretar(None) == {"texto": None, "campos": [], "tabelas": []}


def test_composicao_numerador_denominador():
    assert D.composicao(LINHA) == "R$ 4.362.789,11 de R$ 39.681.681,48 = 11,0%"
    assert D.composicao({**LINHA, "denominador": 0}) is None and D.composicao({"numerador": 1}) is None
    assert D.composicao({"numerador": 5, "denominador": 10, "unidade": "un"}) == "5,00 de 10,00 = 50,0%"


def test_avisos_variacao_e_faixa_90():
    interp = D.interpretar(I27)
    hist = [{"periodo": "2026-08", "realizado": 1000000.0, "empresa": "", "obra": "", "un": ""}, {"periodo": "2026-09", "realizado": 2000000.0, "empresa": "", "obra": "", "un": ""},
            {"periodo": "2026-10", "realizado": 4362789.11, "empresa": "", "obra": "", "un": ""}, {"periodo": "2026-09", "realizado": 9.0, "empresa": "X", "obra": "", "un": ""}]
    av = D.avisos(LINHA, interp, hist)
    assert any("+118,1%" in a and "09/2026" in a for a in av)                # compara com o mes anterior da MESMA empresa/obra/UN
    assert any("24,8%" in a and "Mais de 90 dias" in a for a in av)
    # variacao pequena: sem aviso de variacao
    av2 = D.avisos({**LINHA, "realizado": 2100000.0}, {"tabelas": []}, hist)
    assert av2 == []
    # mes anterior zero e agora tem valor
    assert "era zero" in D.avisos(LINHA, {"tabelas": []}, [{"periodo": "2026-09", "realizado": 0.0}])[0]
    # sem historico ou sem valor: nada a avisar, sem erro
    assert D.avisos(LINHA, {"tabelas": []}, None) == [] and D.avisos({"periodo": "2026-10"}, {"tabelas": []}, hist) == []
