# -*- coding: utf-8 -*-
"""Diretor.IA - DADOS do relatorio PDF (modulo puro: sem Streamlit, sem banco e sem PDF). Junta o que o painel ja mostra (catalogo + metricas gravadas pelos apps de
origem + pendencias) num dicionario simples que relatorio_pdf.py desenha. Nao recalcula indicador: so' organiza, formata e escreve a "leitura padrao" por modelo
(texto fixo preenchido com os numeros; nenhuma IA escreve o relatorio)."""
from __future__ import annotations

import catalogo
import detalhe
import metricas_dados as md
import painel
import reports
from formatacao import numero_br, pct_br, primeiro_nome, valor_com_unidade

SECOES = {"resumo": "Resumo executivo", "atencao": "Pontos de atenção", "indicadores": "Indicadores por categoria", "detalhes": "Detalhe dos indicadores",
          "entregaveis": "Entregáveis", "pendencias": "Reports e pendências"}
MAX_DETALHES = 10
ORDEM_URG = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}


def _status_txt(s: str) -> str:
    """'🔴 Fora da meta' -> 'Fora da meta'."""
    return s.split(" ", 1)[1] if " " in s else s


def leitura_padrao(resumo: dict, cats: list, pend: dict | None) -> list:
    """Paragrafos de leitura do resumo (modelo fixo preenchido com numeros do painel). Lista de textos."""
    st = resumo["status_indicadores"]
    n, com = resumo["indicadores"], resumo["ind_com_valor"]
    p1 = (f"A matriz tem {n} indicadores e {resumo['entregas']} entregáveis. {com} indicadores ({numero_br(100.0 * com / n, 0) if n else '0'}%) já têm valor gravado pelos apps de origem; "
          f"{n - com} ainda aguardam o primeiro valor (estado «Sem lançamento», que não significa resultado ruim).")
    p2 = (f"Entre os indicadores com valor: {st.get('No alvo', 0)} no alvo, {st.get('Atenção', 0)} em atenção, {st.get('Fora da meta', 0)} fora da meta e "
          f"{st.get('Sem meta', 0)} apenas informativos (o app de origem ainda não tem meta numérica para julgar).")
    saida = [p1, p2]
    pior = [c for c in cats if c["🔴 Fora da meta"] or c["🟡 Atenção"]]
    if pior:
        pior = sorted(pior, key=lambda c: -(c["🔴 Fora da meta"] * 2 + c["🟡 Atenção"]))[:3]
        saida.append("Categorias que mais pedem atenção: " + "; ".join(f"{c['Categoria']} ({c['🔴 Fora da meta']} fora da meta, {c['🟡 Atenção']} em atenção)" for c in pior) + ".")
    if pend is not None:
        k = pend["kpis"]
        saida.append(f"Pendências relatadas pelos colaboradores: {k['abertas']} em aberto, sendo {k['urgentes']} urgentes (alta ou crítica) e {k['criticas']} críticas; "
                     f"{k['resolvidas_30d']} foram resolvidas nos últimos 30 dias.")
    return saida


def _detalhe_do_item(item: dict, linhas: list, hist: list) -> dict:
    hist_item = [h for h in (hist or []) if h.get("item_id") == item["item_id"]]
    blocos = []
    for l in linhas[:3]:
        interp = detalhe.interpretar(l.get("detalhe"))
        blocos.append({"empresa": l.get("empresa") or "", "obra": l.get("obra") or "", "un": l.get("un") or "", "periodo": md.periodo_br(l.get("periodo")),
                       "valor": valor_com_unidade(l.get("realizado"), l.get("unidade")), "meta": valor_com_unidade(l.get("meta"), l.get("unidade")),
                       "pct": pct_br(l.get("pct_atingimento")), "composicao": detalhe.composicao(l), "avisos": detalhe.avisos(l, interp, hist_item),
                       "campos": interp["campos"], "tabelas": interp["tabelas"], "texto": (interp["texto"] or "")[:600] or None})
    return {"id": item["item_id"], "nome": item["nome"], "categoria": item.get("categoria") or "—", "status": md.status_do_item(linhas), "blocos": blocos,
            "mais_linhas": max(0, len(linhas) - 3)}


def escolher_detalhes(itens: list, por_item: dict, hist: list, pedidos: list | None) -> list:
    """Indicadores que ganham pagina de detalhe: os pedidos pelo usuario (na ordem) ou, sem pedido, os que estao fora da meta/atencao ou tem aviso de numero fora do comum."""
    ind = {i["item_id"]: i for i in catalogo.indicadores(itens)}
    if pedidos:
        ids = [x for x in pedidos if x in ind and por_item.get(x)]
    else:
        ids = []
        for i in catalogo.indicadores(itens):
            linhas = por_item.get(i["item_id"], [])
            if not linhas:
                continue
            ruim = md.status_do_item(linhas) in ("Fora da meta", "Atenção")
            aviso = any(detalhe.avisos(l, detalhe.interpretar(l.get("detalhe")), [h for h in (hist or []) if h.get("item_id") == i["item_id"]]) for l in linhas[:3])
            if ruim or aviso:
                ids.append(i["item_id"])
    return [_detalhe_do_item(ind[x], por_item[x], hist) for x in ids[:MAX_DETALHES]]


def dados_pendencias(itens_pend: list, hoje) -> dict:
    ab = reports.abertas(itens_pend)
    ab = sorted(ab, key=lambda i: (ORDEM_URG.get(i["urgencia"], 9), -i["semana_de"].toordinal(), -i["id"]))
    linhas = [{"n": i["id"], "colaborador": i["colaborador"] if i["colaborador"] == reports.SEM_NOME else primeiro_nome(i["colaborador"]), "tipo": reports.TIPOS.get(i["tipo"], i["tipo"]),
               "urgencia": reports.URGENCIAS.get(i["urgencia"], i["urgencia"]), "urg_chave": i["urgencia"], "situacao": reports.SITUACOES.get(i["situacao"], i["situacao"]),
               "titulo": i.get("titulo") or "(sem título)", "vinculo": i.get("vinculo_item_id") or "", "semana": i["semana_de"].strftime("%d/%m/%Y")} for i in ab]
    pc = reports.abertas_por_colaborador(itens_pend)
    por_colab = {}
    for nome, lin in (pc.iterrows() if len(pc) else []):
        k = nome if nome == reports.SEM_NOME else primeiro_nome(nome)
        por_colab[k] = por_colab.get(k, 0) + int(lin.sum())
    return {"kpis": reports.kpis(itens_pend, hoje), "linhas": linhas, "por_colaborador": sorted(por_colab.items(), key=lambda x: -x[1])}


def montar(itens: list, por_item: dict, hist: list, itens_pend: list | None, opcoes: dict, gerado_em) -> dict:
    """Tudo que o PDF precisa. opcoes: secoes (lista de chaves de SECOES), detalhe_ids (opcional), observacao (texto do Diretor, opcional)."""
    secoes = [s for s in SECOES if s in (opcoes.get("secoes") or list(SECOES))]
    resumo = painel.resumo_geral(itens, por_item)
    cats = painel.resumo_por_categoria(itens, por_item)
    todas = [l for ls in por_item.values() for l in ls]
    ps = [l.get("periodo") for l in todas if l.get("periodo")]
    pend = dados_pendencias(itens_pend, gerado_em.date()) if (itens_pend is not None and "pendencias" in secoes) else None
    linhas_ind = painel.tabela_indicadores(itens, por_item)
    return {
        "gerado_em": gerado_em, "periodo_ref": md.periodo_br(max(ps)) if ps else "—", "matriz": catalogo.versao_matriz(itens), "secoes": secoes, "resumo": resumo, "categorias": cats,
        "leitura": leitura_padrao(resumo, cats, pend), "observacao": (opcoes.get("observacao") or "").strip()[:2000],
        "atencao": [{**l, "Status": _status_txt(l["Status"])} for l in painel.pontos_de_atencao(itens, por_item)] if "atencao" in secoes else [],
        "indicadores": [{**l, "Status": _status_txt(l["Status"])} for l in linhas_ind] if "indicadores" in secoes else [],
        "detalhes": escolher_detalhes(itens, por_item, hist, opcoes.get("detalhe_ids")) if "detalhes" in secoes else [],
        "entregas": [{**l, "Status": _status_txt(l["Status"])} for l in painel.tabela_entregas(itens, por_item)] if "entregaveis" in secoes else [],
        "pendencias": pend,
    }
