# -*- coding: utf-8 -*-
"""Diretor.IA - catalogo dos 54 indicadores e 44 entregas (tabela diretoria.catalogo_item, carregada da matriz do ENERDATA). So leitura."""
from __future__ import annotations

# Ordem de exibicao das categorias (nomes de categoria nao sao dado pessoal). Categoria nova no banco entra no fim.
ORDEM_CATEGORIAS = [
    "Resultado e margem", "Obras e projeção", "Caixa e liquidez", "Dívida e endividamento", "Contábil e retorno",
    "Recebíveis e pagáveis", "Fiscal", "Notas fiscais de entrada", "Pessoas", "Automação e painéis",
]

_SQL = """SELECT item_id, tipo, nome, categoria, responsavel, app_origem, situacao, periodicidade, meta, referencia, apuracao, fonte,
                 indicador_ref, ordem, versao_matriz, carregado_em
          FROM diretoria.catalogo_item WHERE ativo ORDER BY tipo, ordem, item_id"""


def carregar(banco) -> list:
    """Todos os itens ativos do catalogo (indicadores e entregas)."""
    return banco.consultar(_SQL)


def indicadores(itens) -> list:
    return [i for i in itens if i.get("tipo") == "indicador"]


def entregas(itens) -> list:
    return [i for i in itens if i.get("tipo") == "entrega"]


def categorias_em_ordem(itens) -> list:
    """Categorias existentes nos indicadores, na ordem de exibicao."""
    existentes = {i.get("categoria") for i in indicadores(itens) if i.get("categoria")}
    base = [c for c in ORDEM_CATEGORIAS if c in existentes]
    return base + sorted(existentes - set(base))


def por_categoria(itens) -> dict:
    """{categoria: [indicadores...]} na ordem de exibicao."""
    ind = indicadores(itens)
    return {c: [i for i in ind if i.get("categoria") == c] for c in categorias_em_ordem(itens)}


def versao_matriz(itens) -> str:
    vs = sorted({i.get("versao_matriz") for i in itens if i.get("versao_matriz")})
    return ", ".join(vs) if vs else "—"
