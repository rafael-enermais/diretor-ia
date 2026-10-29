# -*- coding: utf-8 -*-
import pathlib
import re

import chat_ferramentas as FERR
import guia_app as G
from fakes import BancoFalso

APP = pathlib.Path(__file__).resolve().parent.parent / "app" / "app.py"


def test_toda_tela_do_menu_tem_verbete_no_guia():
    titulos = re.findall(r'st\.Page\("[^"]+", title="([^"]+)"', APP.read_text(encoding="utf-8"))
    assert len(titulos) >= 8
    menus = {p["menu"] for p in G.PAGINAS}
    faltam = [t for t in titulos if t not in menus]
    assert not faltam, f"telas do menu sem verbete em guia_app.py: {faltam}"


def test_guia_admin_so_para_admin_e_busca():
    assert G.pagina("logs", admin=False) is None and G.pagina("Logs (admin)", admin=True)["so_admin"] is True
    assert all(not p.get("so_admin") for p in G.paginas(False))
    assert G.pagina("Reports e pendências")["pagina"] == "reports" and G.pagina("categorias")["titulo"].startswith("Categorias")
    r = G.buscar("como exporto as pendências para planilha")
    assert r["paginas"] and r["paginas"][0]["pagina"] == "reports" and any("planilha" in (a + b).lower() for a, b in r["perguntas"])
    assert G.buscar("") == {"paginas": [], "glossario": [], "perguntas": []}


def test_ferramenta_como_usar_o_app():
    ctx = FERR.Contexto(BancoFalso(), [], {}, papel="diretor")
    r, _ = FERR.executar(ctx, "como_usar_o_app", {"pagina": "vinculos"})
    assert "Confirmar" in " ".join(r["pagina"]["como"])
    r, _ = FERR.executar(ctx, "como_usar_o_app", {"busca": "o que significa o aviso 👀 de variação"})
    assert r["termos"] and r["termos"][0]["termo"].startswith("Aviso")
    r, _ = FERR.executar(ctx, "como_usar_o_app", {"pagina": "logs"})                      # diretor nao enxerga a tela de admin
    assert "registro de eventos e erros" not in str(r)
    r, _ = FERR.executar(FERR.Contexto(BancoFalso(), [], {}, papel="admin"), "como_usar_o_app", {"pagina": "logs"})
    assert "E-DIRETOR" in r["pagina"]["serve"]
    r, _ = FERR.executar(ctx, "como_usar_o_app", {"busca": "zzzxxx"})
    assert "Nada no guia" in r["observacao"]
