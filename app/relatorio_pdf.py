# -*- coding: utf-8 -*-
"""Diretor.IA - gerador do RELATORIO PDF da Diretoria Financeira (A4, mesmo padrao visual do GDF e do EGC: Poppins, azul #171C60 e laranja, logo, marca-d'agua).
Desenha o dicionario pronto de relatorio_dados.montar (nenhum calculo aqui). O PDF e' feito em memoria (bytes): nada vai para o disco.
Layout em 2 passadas: a 1a conta as paginas (para o 'Pagina n de N'), a 2a desenha de verdade. Texto com caractere que a fonte nao tem (ex.: emoji) e' limpo antes de desenhar."""
from __future__ import annotations

import io
import threading
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from formatacao import numero_br

ASSETS = Path(__file__).resolve().parent / "assets_relatorio"
_LOCK = threading.Lock()
_FONTES = False

NAVY = HexColor("#171C60"); ORANGE = HexColor("#EA9527"); BRAND_OR = HexColor("#F99D20")
GREY = HexColor("#525252"); GREY_BG = HexColor("#F6F8FB"); BORDER = HexColor("#DADFE8"); WHITE = HexColor("#FFFFFF")
NEG_TXT = HexColor("#9A5200"); POS_TXT = HexColor("#1A7A3C"); MID = HexColor("#5C6091"); LIGHT = HexColor("#B4B9D6"); AMBER = HexColor("#B7791F"); RED = HexColor("#C0392B")
COR_STATUS = {"No alvo": POS_TXT, "Atenção": AMBER, "Fora da meta": RED, "Sem meta": MID, "Sem lançamento": GREY}
FILL_STATUS = {"No alvo": HexColor("#2E9E5B"), "Atenção": HexColor("#F2B134"), "Fora da meta": HexColor("#D64545"), "Sem meta": HexColor("#5C6091"), "Sem lançamento": HexColor("#C9CCD8")}
COR_URG = {"critica": RED, "alta": HexColor("#C2631D"), "media": AMBER, "baixa": GREY}
W, H = 595.28, 841.89
MX = 40.0
CW = W - 2 * MX
TOPY = H - 84
LIMITE_Y = 52.0                  # abaixo disso, nova pagina


def _registrar_fontes():
    global _FONTES
    if _FONTES:
        return
    for n, f in [("P", "Poppins-Regular"), ("PM", "Poppins-Medium"), ("PB", "Poppins-Bold"), ("PI", "Poppins-Italic")]:
        pdfmetrics.registerFont(TTFont(n, str(ASSETS / "fonts" / (f + ".ttf"))))
    _FONTES = True


def L(s) -> str:
    """Texto seguro para a fonte: tira o que a Poppins nao desenha (emoji etc.) e troca setas/sinais comuns."""
    t = str(s if s is not None else "").replace("→", "para").replace("≥", ">=").replace("≤", "<=").replace(" ", " ").replace("\t", " ")
    mapa = pdfmetrics.getFont("P").face.charToGlyph
    return "".join(ch for ch in t if ord(ch) in mapa or ch in " \n").replace("  ", " ").strip()


class Doc:
    def __init__(self, c, ctx: dict, N: int):
        self.c, self.ctx, self.N, self.n, self.secao, self.y = c, ctx, N, 0, "", TOPY

    def pagina(self, secao: str):
        if self.n:
            self.c.showPage()
        self.n += 1
        self.secao = secao
        moldura(self, secao)
        self.y = TOPY

    def garantir(self, h: float, cabecalho=None):
        """Se nao cabe `h` pontos, abre pagina nova (mesma secao) e redesenha o cabecalho da tabela, se houver."""
        if self.y - h < LIMITE_Y:
            self.pagina(self.secao)
            if cabecalho:
                cabecalho()


# ------------------------------------------------------------------ primitivos
def txt(c, x, y, s, font="P", size=8, color=GREY, al="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    s = L(s)
    if al == "l":
        c.drawString(x, y, s)
    elif al == "r":
        c.drawRightString(x, y, s)
    else:
        c.drawCentredString(x, y, s)


def rect(c, x, y, w, h, fill=None, stroke=None, r=0, lw=0.6):
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
    if r:
        c.roundRect(x, y, w, h, r, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)
    else:
        c.rect(x, y, w, h, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def hline(c, x1, x2, y, color=BORDER, lw=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x1, y, x2, y)


def linhas_de(s, font, size, w, maximo=None):
    out = []
    for bloco in L(s).split("\n"):
        out += simpleSplit(bloco, font, size, w) or [""]
    if maximo and len(out) > maximo:
        out = out[:maximo]
        while out[-1] and pdfmetrics.stringWidth(out[-1] + "…", font, size) > w:
            out[-1] = out[-1][:-1]
        out[-1] = out[-1].rstrip() + "…"
    return out


def para(doc, s, x=MX, w=CW, size=8.4, lead=12.6, gap=6, color=GREY, font="P"):
    for bloco in str(s).split("\n"):
        for ln in linhas_de(bloco, font, size, w):
            doc.garantir(lead)
            txt(doc.c, x, doc.y, ln, font, size, color)
            doc.y -= lead
        doc.y -= gap


def titulo(doc, t, sub=None):
    doc.garantir(40)
    txt(doc.c, MX, doc.y, t, "PB", 15, NAVY)
    if sub:
        txt(doc.c, MX, doc.y - 15, sub, "P", 8, GREY)
    doc.y -= 32 if sub else 22


def subtitulo(doc, t, extra=None):
    doc.garantir(30)
    txt(doc.c, MX, doc.y, t, "PB", 9.5, NAVY)
    if extra:
        txt(doc.c, W - MX, doc.y, extra, "P", 7, GREY, "r")
    doc.y -= 15


def caixa(doc, s, fill=GREY_BG, borda=BORDER, size=7.8, titulo_=None):
    ls = linhas_de(s, "P", size, CW - 22)
    h = len(ls) * (size + 3.6) + 14 + (11 if titulo_ else 0)
    doc.garantir(h + 8)
    rect(doc.c, MX, doc.y - h, CW, h, fill=fill, stroke=borda, r=5, lw=0.5)
    yy = doc.y - 14
    if titulo_:
        txt(doc.c, MX + 11, yy, titulo_, "PB", 7.4, NAVY)
        yy -= 11
    for ln in ls:
        txt(doc.c, MX + 11, yy, ln, "P", size, GREY)
        yy -= size + 3.6
    doc.y -= h + 8


def kpi(c, x, y, w, h, rot, valor, sub, dark=False, accent=None):
    if dark:
        rect(c, x, y - h, w, h, fill=NAVY, r=6)
        txt(c, x + 11, y - 15, rot.upper(), "PB", 6.2, BRAND_OR)
        txt(c, x + 11, y - 36, valor, "PB", 15, WHITE)
        for i, ln in enumerate(linhas_de(sub, "P", 6.4, w - 24, 2)):
            txt(c, x + 11, y - 49 - i * 8.4, ln, "P", 6.4, HexColor("#D6D9EA"))
    else:
        rect(c, x, y - h, w, h, fill=GREY_BG, r=4)
        rect(c, x, y - h, 3, h, fill=accent or NAVY)
        txt(c, x + 11, y - 14, rot.upper(), "PB", 6.2, accent or NAVY)
        txt(c, x + 11, y - 35, valor, "PB", 15, NAVY)
        for i, ln in enumerate(linhas_de(sub, "P", 6.4, w - 24, 2)):
            txt(c, x + 11, y - 48 - i * 8.4, ln, "P", 6.4, GREY)


def kpis_linha(doc, cartoes, h=62):
    doc.garantir(h + 10)
    n = len(cartoes)
    gap = 8
    w = (CW - gap * (n - 1)) / n
    for i, (rot, valor, sub, dark, accent) in enumerate(cartoes):
        kpi(doc.c, MX + i * (w + gap), doc.y, w, h, rot, valor, sub, dark, accent)
    doc.y -= h + 12


def tabela(doc, cols, header, rows, fs=6.9, maxl=3):
    """cols: [(largura, 'l'|'r')]. rows: ('sec', texto) | ('lin', [celula...]) com celula = texto ou (texto, cor). Quebra de pagina com cabecalho repetido; texto longo quebra em ate `maxl` linhas."""
    tw = sum(w for w, _ in cols)

    def cab():
        h = 20
        rect(doc.c, MX, doc.y - h, tw, h, fill=NAVY)
        x = MX
        for (w, al), t in zip(cols, header):
            ls = linhas_de(t, "PB", 6.4, w - 8, 2)
            for k, ln in enumerate(ls):
                yy = doc.y - 9 - k * 7.4 + (3.2 if len(ls) == 1 else 0)
                txt(doc.c, x + 4 if al == "l" else x + w - 4, yy, ln, "PB", 6.4, WHITE, "l" if al == "l" else "r")
            x += w
        doc.y -= h
    doc.garantir(20 + 22, None)
    cab()
    for tipo, cel in rows:
        if tipo == "sec":
            doc.garantir(34, cab)
            rect(doc.c, MX, doc.y - 15, tw, 15, fill=HexColor("#E8EAF3"))
            txt(doc.c, MX + 5, doc.y - 10.6, cel, "PB", 7.2, NAVY)
            doc.y -= 15
            continue
        quebras = []
        for (w, al), c_ in zip(cols, cel):
            s = c_[0] if isinstance(c_, tuple) else c_
            quebras.append(linhas_de(s, "P", fs, w - 8, maxl) if al == "l" else [L(s)])
        h = max(len(q) for q in quebras) * (fs + 1.9) + 5
        doc.garantir(h + 2, cab)
        x = MX
        for (w, al), c_, q in zip(cols, cel, quebras):
            cor = c_[1] if isinstance(c_, tuple) and c_[1] is not None else GREY
            font = "PB" if isinstance(c_, tuple) and c_[1] is not None else "P"
            for k, ln in enumerate(q):
                yy = doc.y - 3 - fs - k * (fs + 1.9)
                doc.c.setFont(font, fs)
                doc.c.setFillColor(cor)
                (doc.c.drawString(x + 4, yy, ln) if al == "l" else doc.c.drawRightString(x + w - 4, yy, ln))
            x += w
        hline(doc.c, MX, MX + tw, doc.y - h, HexColor("#EEF0F6"), 0.4)
        doc.y -= h
    doc.y -= 10


def barra_empilhada(doc, partes, legenda=True):
    """partes: [(rotulo, valor, cor)] ; largura proporcional ao total."""
    total = sum(v for _, v, _ in partes) or 1
    doc.garantir(34)
    x = MX
    for rot, v, cor in partes:
        w = v / total * CW
        if w > 0:
            rect(doc.c, x, doc.y - 12, max(w - 1.2, 0.6), 12, fill=cor)
        x += w
    doc.y -= 24
    if legenda:
        x = MX
        for rot, v, cor in partes:
            rect(doc.c, x, doc.y - 1, 7, 7, fill=cor)
            txt(doc.c, x + 11, doc.y, f"{rot}: {v}", "P", 6.8, GREY)
            x += 22 + pdfmetrics.stringWidth(L(f"{rot}: {v}"), "P", 6.8) + 8
        doc.y -= 16


def barras_h(doc, itens, cor=MID, rot_w=150, fmt=lambda v: numero_br(v, 0), cores=None):
    """itens: [(rotulo, valor)]; barra proporcional ao maior valor."""
    if not itens:
        return
    mx = max(v for _, v in itens) or 1
    bw = CW - rot_w - 70
    doc.garantir(13.5 * len(itens) + 8)  # o grafico inteiro fica na mesma pagina
    for i, (rot, v) in enumerate(itens):
        doc.garantir(14)
        r = L(rot)
        if pdfmetrics.stringWidth(r, "P", 6.9) > rot_w - 6:
            while len(r) > 2 and pdfmetrics.stringWidth(r + "…", "P", 6.9) > rot_w - 6:
                r = r[:-1]
            r = r.rstrip() + "…"
        txt(doc.c, MX, doc.y, r, "P", 6.9, GREY)
        rect(doc.c, MX + rot_w, doc.y - 1.5, max(bw * v / mx, 0.8), 7.2, fill=(cores[i] if cores else cor))
        txt(doc.c, W - MX, doc.y, fmt(v), "PB", 6.9, NAVY, "r")
        doc.y -= 13.5
    doc.y -= 6


# ------------------------------------------------------------------ moldura e capa
def moldura(doc, secao):
    c, ctx = doc.c, doc.ctx
    wm = ImageReader(str(ASSETS / "torre_watermark.png"))
    c.drawImage(wm, W / 2 - 170, 28, width=340, height=343, mask="auto")
    rect(c, 0, H - 4, W * 0.62, 4, fill=NAVY)
    rect(c, W * 0.62, H - 4, W * 0.38, 4, fill=ORANGE)
    lg = ImageReader(str(ASSETS / "logo_enermais_app.png"))
    iw, ih = lg.getSize()
    c.drawImage(lg, MX, H - 50, width=30 * iw / ih, height=30, mask="auto")
    txt(c, W - MX, H - 28, f"RELATÓRIO DA DIRETORIA FINANCEIRA · {ctx['periodo_ref']}", "PB", 6.4, NAVY, "r")
    txt(c, W - MX, H - 39, secao, "PB", 8, NAVY, "r")
    hline(c, MX, W - MX, H - 58, BORDER, 0.6)
    hline(c, MX, W - MX, 38, BORDER, 0.5)
    txt(c, MX, 26, "Gerado em " + ctx["gerado_em"].strftime("%d/%m/%Y %H:%M"), "PB", 6, ORANGE)
    txt(c, W / 2, 26, f"Página {doc.n} de {doc.N}", "P", 6.8, GREY, "c")
    txt(c, W - MX, 26, "Diretor.IA · Grupo Enermais", "P", 6, GREY, "r")


def capa(doc):
    c, ctx = doc.c, doc.ctx
    doc.n += 1
    c.setFillColor(NAVY)
    p = c.beginPath()
    p.moveTo(W * 0.80, H)
    p.lineTo(W, H)
    p.lineTo(W, 0)
    p.lineTo(W * 0.60, 0)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    mk = ImageReader(str(ASSETS / "capa_marca_pale.png"))
    c.saveState()
    c.setFillAlpha(0.10)
    c.drawImage(mk, W * 0.66, 60, width=250, height=250 * 1409 / 983, mask="auto")
    c.restoreState()
    rect(c, 0, H - 4, W * 0.80, 4, fill=NAVY)
    lg = ImageReader(str(ASSETS / "logo_enermais_app.png"))
    iw, ih = lg.getSize()
    c.drawImage(lg, MX + 8, H - 330, width=215, height=215 * ih / iw, mask="auto")
    rect(c, MX + 8, 405, 52, 3, fill=ORANGE)
    txt(c, MX + 8, 372, "Relatório da", "PB", 27, NAVY)
    txt(c, MX + 8, 342, "Diretoria Financeira", "PB", 27, NAVY)
    txt(c, MX + 8, 312, "Indicadores, entregáveis e pendências", "P", 9.5, GREY)
    txt(c, MX + 8, 297, "Matriz de metas " + str(ctx["matriz"]), "P", 9.5, GREY)
    txt(c, MX + 8, 282, "Posição em " + ctx["gerado_em"].strftime("%d/%m/%Y"), "P", 9.5, GREY)
    rect(c, MX + 8, 238, 252, 24, fill=ORANGE, r=12)
    txt(c, MX + 8 + 126, 246.5, "PERÍODO MAIS RECENTE · " + ctx["periodo_ref"], "PB", 7.6, WHITE, "c")
    g = ImageReader(str(ASSETS / "GRUPO.png"))
    gw, gh = g.getSize()
    c.drawImage(g, MX + 8, 84, width=84, height=84 * gh / gw, mask="auto")
    txt(c, MX + 8, 70, "Informações reunidas pelo painel Diretor.IA a partir dos apps de origem (GDF, EGC e outros).", "P", 6.4, GREY)
    txt(c, MX + 8, 26, "Gerado em " + ctx["gerado_em"].strftime("%d/%m/%Y %H:%M"), "PB", 6, ORANGE)


# ------------------------------------------------------------------ secoes
def sec_resumo(doc):
    ctx = doc.ctx
    r, st = ctx["resumo"], ctx["resumo"]["status_indicadores"]
    doc.pagina("Resumo executivo")
    titulo(doc, "Resumo executivo", f"Período mais recente com dado: {ctx['periodo_ref']} · valores gravados pelos apps de origem")
    n = r["indicadores"] or 1
    cart = [("Indicadores com valor", f"{r['ind_com_valor']} de {r['indicadores']}", f"{numero_br(100.0 * r['ind_com_valor'] / n, 0)}% da matriz", True, None),
            ("No alvo", str(st.get("No alvo", 0)), "dentro da meta", False, FILL_STATUS["No alvo"]),
            ("Atenção", str(st.get("Atenção", 0)), "perto do limite da meta", False, FILL_STATUS["Atenção"]),
            ("Fora da meta", str(st.get("Fora da meta", 0)), "pedem conversa com o responsável", False, FILL_STATUS["Fora da meta"])]
    kpis_linha(doc, cart)
    p = ctx["pendencias"]
    cart2 = [("Entregáveis com resultado", f"{r['ent_com_valor']} de {r['entregas']}", "resultado já gravado", True, None)]
    if p:
        k = p["kpis"]
        cart2 += [("Pendências em aberto", str(k["abertas"]), f"{k['colaboradores_com_aberta']} colaboradores com item aberto", False, MID),
                  ("Urgentes (alta/crítica)", str(k["urgentes"]), f"{k['criticas']} críticas", False, RED), ("Resolvidas (30 dias)", str(k["resolvidas_30d"]), "marcadas como resolvidas", False, FILL_STATUS["No alvo"])]
    else:
        cart2 += [("Só informativos", str(st.get("Sem meta", 0)), "valor sem meta numérica", False, MID), ("Sem lançamento", str(st.get("Sem lançamento", 0)), "ainda sem valor gravado", False, GREY)]
    kpis_linha(doc, cart2)
    subtitulo(doc, "Situação dos indicadores")
    barra_empilhada(doc, [(k_, st.get(k_, 0), FILL_STATUS[k_]) for k_ in ("No alvo", "Atenção", "Fora da meta", "Sem meta", "Sem lançamento")])
    subtitulo(doc, "Por categoria")
    cols = [(150, "l"), (52, "r"), (52, "r"), (52, "r"), (52, "r"), (52, "r"), (52, "r"), (53.3, "r")]
    rows = [("lin", [c["Categoria"], str(c["Indicadores"]), str(c["Com valor"]), str(c["🟢 No alvo"]), str(c["🟡 Atenção"]), str(c["🔴 Fora da meta"]),
                     str(c["🔵 Sem meta (informativo)"]), str(c["⚪ Sem lançamento"])]) for c in ctx["categorias"]]
    tabela(doc, cols, ["Categoria", "Indicadores", "Com valor", "No alvo", "Atenção", "Fora da meta", "Informativo", "Sem lançamento"], rows)
    subtitulo(doc, "Leitura")
    for t in ctx["leitura"]:
        para(doc, t, size=8.2, lead=12.2, gap=5)
    if ctx["observacao"]:
        caixa(doc, ctx["observacao"], fill=HexColor("#FFF6E6"), borda=HexColor("#F2D9A8"), titulo_="OBSERVAÇÃO DO DIRETOR")


_COLS_IND = [(34, "l"), (128, "l"), (56, "l"), (46, "l"), (76, "r"), (66, "r"), (42, "r"), (67.3, "l")]
_HEAD_IND = ["ID", "Indicador", "Responsável", "Período", "Valor", "Meta", "% da meta", "Status"]


def _linha_ind(l):
    return ("lin", [l["ID"], l["Indicador"], l["Responsável"], l["Período"], l["Valor"], l["Meta"], l["% da meta"], (l["Status"], COR_STATUS.get(l["Status"], GREY))])


def sec_atencao(doc):
    doc.pagina("Pontos de atenção")
    titulo(doc, "Pontos de atenção", "Indicadores fora da meta ou em atenção, os piores primeiro")
    linhas = doc.ctx["atencao"]
    if not linhas:
        para(doc, "Nenhum indicador fora da meta ou em atenção neste momento.")
        return
    cols = [(34, "l"), (124, "l"), (80, "l"), (46, "l"), (70, "r"), (58, "r"), (42, "r"), (61.3, "l")]
    rows = [("lin", [l["ID"], l["Indicador"], l["Categoria"], l["Período"], l["Valor"], l["Meta"], l["% da meta"], (l["Status"], COR_STATUS.get(l["Status"], GREY))]) for l in linhas]
    tabela(doc, cols, ["ID", "Indicador", "Categoria", "Período", "Valor", "Meta", "% da meta", "Status"], rows)


def sec_indicadores(doc):
    doc.pagina("Indicadores por categoria")
    titulo(doc, "Indicadores por categoria", "Último valor gravado, meta e status de cada indicador (valor e status vêm do app de origem)")
    rows, cat = [], None
    for l in doc.ctx["indicadores"]:
        if l["Categoria"] != cat:
            cat = l["Categoria"]
            rows.append(("sec", cat))
        rows.append(_linha_ind(l))
    tabela(doc, _COLS_IND, _HEAD_IND, rows)


def sec_detalhes(doc):
    det = doc.ctx["detalhes"]
    doc.pagina("Detalhe dos indicadores")
    titulo(doc, "Detalhe dos indicadores", "O que está por trás do número: composição, faixas e avisos de número fora do comum")
    if not det:
        para(doc, "Nenhum indicador selecionado ou com aviso neste momento.")
        return
    for d in det:
        doc.garantir(70)
        rect(doc.c, MX, doc.y - 17, CW, 17, fill=NAVY)
        txt(doc.c, MX + 6, doc.y - 12, f"{d['id']} · {d['nome']}", "PB", 8, WHITE)
        txt(doc.c, W - MX - 6, doc.y - 12, d["status"], "PB", 7.4, HexColor("#FFD9A8"), "r")
        doc.y -= 24
        txt(doc.c, MX, doc.y, d["categoria"], "P", 7, GREY)
        doc.y -= 12
        for b in d["blocos"]:
            nome = " · ".join(x for x in (b["empresa"], b["obra"], b["un"]) if x) or "geral"
            doc.garantir(34)
            txt(doc.c, MX, doc.y, f"{nome} — {b['periodo']}", "PB", 7.6, NAVY)
            txt(doc.c, W - MX, doc.y, f"Valor {b['valor']}   ·   Meta {b['meta']}   ·   % da meta {b['pct']}", "P", 7.2, GREY, "r")
            doc.y -= 13
            if b["composicao"]:
                para(doc, "Composição: " + b["composicao"], size=7.6, lead=11, gap=3, color=NAVY)
            for a in b["avisos"]:
                caixa(doc, a, fill=HexColor("#FFF6E6"), borda=HexColor("#F2D9A8"), size=7.4, titulo_="ATENÇÃO AO NÚMERO")
            if b["campos"]:
                tabela(doc, [(190, "l"), (CW - 190, "l")], ["Campo", "Valor"], [("lin", [r, v]) for r, v in b["campos"]], maxl=2)
            for t in b["tabelas"]:
                ks = list(t["linhas"][0].keys())
                w0 = 150 if len(ks) > 3 else CW * 0.5
                resto = (CW - w0) / max(len(ks) - 1, 1)
                tabela(doc, [(w0, "l")] + [(resto, "r")] * (len(ks) - 1), ks, [("lin", [str(l.get(k_, "")) for k_ in ks]) for l in t["linhas"]])
                pts = [(x["rotulo"], x["valor"]) for x in t["bruto"] if x.get("rotulo") and x.get("valor") is not None]
                if len(pts) >= 2:
                    barras_h(doc, pts, fmt=lambda v: "R$ " + numero_br(v, 2))
            if b["texto"] and not (b["campos"] or b["tabelas"]):
                para(doc, "Como o número foi apurado: " + b["texto"], size=7.2, lead=10.4, gap=3)
        if d["mais_linhas"]:
            para(doc, f"(+ {d['mais_linhas']} linhas por empresa/obra/UN não detalhadas aqui; veja no painel.)", size=7, lead=10, gap=4)
        doc.y -= 8


def sec_entregaveis(doc):
    doc.pagina("Entregáveis")
    titulo(doc, "Entregáveis", "Responsável, prazo, meta e resultado gravado")
    cols = [(32, "l"), (150, "l"), (52, "l"), (60, "l"), (72, "l"), (60, "r"), (28, "r"), (61.3, "l")]
    rows = [("lin", [l["ID"], l["Entrega"], l["Responsável"], l["Prazo"], l["Meta"], l["Resultado"], l["% da meta"], (l["Status"], COR_STATUS.get(l["Status"], GREY))]) for l in doc.ctx["entregas"]]
    tabela(doc, cols, ["ID", "Entrega", "Responsável", "Prazo", "Meta", "Resultado", "% meta", "Status"], rows)


def sec_pendencias(doc):
    p = doc.ctx["pendencias"]
    doc.pagina("Reports e pendências")
    titulo(doc, "Reports e pendências", "O que os colaboradores relataram, por urgência (só os itens em aberto)")
    k = p["kpis"]
    kpis_linha(doc, [("Em aberto", str(k["abertas"]), "nova ou em acompanhamento", True, None), ("Urgentes", str(k["urgentes"]), "alta ou crítica", False, RED),
                     ("Resolvidas (30 dias)", str(k["resolvidas_30d"]), "marcadas como resolvidas", False, FILL_STATUS["No alvo"]),
                     ("Tempo médio", "—" if k["dias_medios_para_resolver"] is None else f"{numero_br(k['dias_medios_para_resolver'], 1)} dias", "para resolver", False, MID)])
    if p["por_colaborador"]:
        subtitulo(doc, "Em aberto por colaborador")
        barras_h(doc, p["por_colaborador"][:12])
    subtitulo(doc, "Itens em aberto")
    if not p["linhas"]:
        para(doc, "Nenhum item em aberto.")
        return
    cols = [(26, "l"), (58, "l"), (62, "l"), (44, "l"), (80, "l"), (34, "l"), (CW - 304, "l")]
    rows = [("lin", [str(l["n"]), l["colaborador"], l["tipo"], (l["urgencia"], COR_URG.get(l["urg_chave"], GREY)), l["situacao"], l["vinculo"], l["titulo"]]) for l in p["linhas"][:80]]
    tabela(doc, cols, ["Nº", "Colaborador", "Tipo", "Urgência", "Situação", "Vínculo", "Título"], rows)
    if len(p["linhas"]) > 80:
        para(doc, f"(Mostrando 80 de {len(p['linhas'])} itens em aberto; veja os demais no painel ou na planilha.)", size=7, lead=10)


def sec_fechamento(doc):
    ctx = doc.ctx
    doc.pagina("Fechamento")
    titulo(doc, "Nota sobre este relatório")
    para(doc, "Os valores, metas e status dos indicadores foram gravados pelos apps de origem (por exemplo, o GDF) e apenas reunidos pelo painel Diretor.IA; o painel não recalcula indicadores. "
              "Os percentuais de composição (numerador ÷ denominador) e a participação de cada faixa são divisões feitas sobre os números gravados, para facilitar a leitura.", size=8.4, lead=12.8, gap=7)
    para(doc, "Os textos de «Leitura» são gerados por modelo padronizado, preenchido com os números do painel. Os avisos de «número fora do comum» são convites para olhar um número "
              "(variação de 30% ou mais frente ao mês anterior; 20% ou mais do vencido há mais de 90 dias) e não substituem a análise do responsável. "
              "Reports e pendências são relatos dos colaboradores, informados como foram recebidos.", size=8.4, lead=12.8, gap=7)
    doc.y -= 40
    y0 = doc.y
    rect(doc.c, MX, y0 - 70, CW, 70, fill=WHITE, stroke=BORDER, r=6)
    lg = ImageReader(str(ASSETS / "logo_enermais_app.png"))
    iw, ih = lg.getSize()
    doc.c.drawImage(lg, MX + 16, y0 - 48, width=40 * iw / ih, height=40, mask="auto")
    tx = MX + 16 + 40 * iw / ih + 16
    txt(doc.c, tx, y0 - 26, "Grupo Enermais — Diretoria Financeira", "PB", 8.4, NAVY)
    txt(doc.c, tx, y0 - 40, "Relatório gerado em " + ctx["gerado_em"].strftime("%d/%m/%Y às %H:%M") + " (horário de Brasília)", "P", 7.2, GREY)
    g_ = ImageReader(str(ASSETS / "GRUPO.png"))
    gw, gh = g_.getSize()
    doc.c.drawImage(g_, W - MX - 16 - 70, y0 - 40, width=70, height=70 * gh / gw, mask="auto")
    txt(doc.c, W / 2, y0 - 90, "Relatório gerado pelo Diretor.IA — painel da Diretoria Financeira · Grupo Enermais", "P", 6.6, GREY, "c")


_SECOES = {"resumo": sec_resumo, "atencao": sec_atencao, "indicadores": sec_indicadores, "detalhes": sec_detalhes, "entregaveis": sec_entregaveis, "pendencias": sec_pendencias}


def _montar(doc):
    capa(doc)
    for chave in doc.ctx["secoes"]:
        if chave == "pendencias" and not doc.ctx.get("pendencias"):
            continue
        _SECOES[chave](doc)
    sec_fechamento(doc)


def gerar_pdf(ctx: dict) -> bytes:
    """PDF em bytes. Duas passadas: conta paginas e desenha."""
    _registrar_fontes()
    with _LOCK:
        seco = Doc(canvas.Canvas(io.BytesIO(), pagesize=(W, H), invariant=1), ctx, 0)
        _montar(seco)
        N = seco.n
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(W, H), invariant=1)
        c.setTitle(f"Relatório da Diretoria Financeira — {ctx['periodo_ref']}")
        c.setAuthor("Grupo Enermais — Diretor.IA")
        c.setSubject("Indicadores, entregáveis e pendências")
        doc = Doc(c, ctx, N)
        _montar(doc)
        c.showPage()
        c.save()
        return buf.getvalue()
