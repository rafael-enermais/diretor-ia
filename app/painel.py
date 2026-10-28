# -*- coding: utf-8 -*-
"""Diretor.IA - monta as tabelas das telas juntando CATALOGO (quem/onde/situacao) + METRICAS (valor/status). Puro: sem Streamlit, sem banco."""
from __future__ import annotations

import catalogo
import metricas_dados as md
from formatacao import primeiros_nomes, status_com_icone, valor_com_unidade, pct_br
from fuso import fmt_br


def _valor_do_item(linhas):
    """(valor_texto, meta_texto, pct_texto) de um item. 1 linha: o que o GDF gravou. Varias linhas: 'N linhas' (nao soma, nao recalcula)."""
    if not linhas:
        return "—", "—", "—"
    if len(linhas) > 1:
        return f"{len(linhas)} linhas (ver detalhe)", "—", "—"
    l = linhas[0]
    un = l.get("unidade")
    return valor_com_unidade(l.get("realizado"), un), valor_com_unidade(l.get("meta"), un), pct_br(l.get("pct_atingimento"))


def linha_indicador(item: dict, linhas_metrica) -> dict:
    valor, meta, pct = _valor_do_item(linhas_metrica)
    return {
        "ID": item.get("item_id"),
        "Indicador": item.get("nome"),
        "Categoria": item.get("categoria") or "—",
        "Responsável": primeiros_nomes(item.get("responsavel")),
        "Situação no app": item.get("situacao") or "—",
        "Período": md.periodo_br(md.periodo_recente(linhas_metrica)),
        "Valor": valor,
        "Meta": meta,
        "% da meta": pct,
        "Status": status_com_icone(md.status_do_item(linhas_metrica)),
        "Atualizado": fmt_br(md.ultima_atualizacao(linhas_metrica)),
    }


def linha_entrega(item: dict, linhas_metrica) -> dict:
    valor, _meta, pct = _valor_do_item(linhas_metrica)
    return {
        "ID": item.get("item_id"),
        "Entrega": item.get("nome"),
        "Responsável": primeiros_nomes(item.get("responsavel")),
        "Prazo": item.get("periodicidade") or "—",
        "Meta": item.get("meta") or "—",
        "Apuração": item.get("apuracao") or "—",
        "Período": md.periodo_br(md.periodo_recente(linhas_metrica)),
        "Resultado": valor,
        "% da meta": pct,
        "Status": status_com_icone(md.status_do_item(linhas_metrica)),
    }


def tabela_indicadores(itens, por_item: dict, categoria: str | None = None) -> list:
    ind = catalogo.indicadores(itens)
    if categoria:
        ind = [i for i in ind if i.get("categoria") == categoria]
    return [linha_indicador(i, por_item.get(i.get("item_id"), [])) for i in ind]


def tabela_entregas(itens, por_item: dict) -> list:
    return [linha_entrega(e, por_item.get(e.get("item_id"), [])) for e in catalogo.entregas(itens)]


def resumo_geral(itens, por_item: dict) -> dict:
    """Numeros da Visao geral: totais, quantos ja tem valor, contagem por status."""
    ind, ent = catalogo.indicadores(itens), catalogo.entregas(itens)
    st_ind = [md.status_do_item(por_item.get(i["item_id"], [])) for i in ind]
    st_ent = [md.status_do_item(por_item.get(e["item_id"], [])) for e in ent]
    return {
        "indicadores": len(ind), "entregas": len(ent),
        "ind_com_valor": sum(1 for s in st_ind if s != "Sem lançamento"),
        "ent_com_valor": sum(1 for s in st_ent if s != "Sem lançamento"),
        "status_indicadores": md.contar_status(st_ind),
        "status_entregas": md.contar_status(st_ent),
    }


def resumo_por_categoria(itens, por_item: dict) -> list:
    """Uma linha por categoria: total, com valor e contagem por status."""
    saida = []
    for cat, ind in catalogo.por_categoria(itens).items():
        sts = [md.status_do_item(por_item.get(i["item_id"], [])) for i in ind]
        c = md.contar_status(sts)
        saida.append({"Categoria": cat, "Indicadores": len(ind), "Com valor": sum(v for k, v in c.items() if k != "Sem lançamento"),
                      "🟢 No alvo": c["No alvo"], "🟡 Atenção": c["Atenção"], "🔴 Fora da meta": c["Fora da meta"], "⚪ Sem lançamento": c["Sem lançamento"]})
    return saida


def linhas_detalhe(linhas_metrica) -> list:
    """Linhas (empresa/obra/UN) de um indicador, para o detalhe da tela de categorias."""
    saida = []
    for l in linhas_metrica or []:
        un = l.get("unidade")
        saida.append({
            "Período": md.periodo_br(l.get("periodo")), "Empresa": l.get("empresa") or "—", "Obra": l.get("obra") or "—", "UN": l.get("un") or "—",
            "Origem do app": l.get("app_origem") or "—", "Previsto": valor_com_unidade(l.get("previsto"), un),
            "Realizado": valor_com_unidade(l.get("realizado"), un), "Meta": valor_com_unidade(l.get("meta"), un),
            "% da meta": pct_br(l.get("pct_atingimento")), "Status": status_com_icone(l.get("status")),
            "Como foi apurado": l.get("origem") or "—", "Atualizado": fmt_br(l.get("atualizado_em")),
        })
    return saida
