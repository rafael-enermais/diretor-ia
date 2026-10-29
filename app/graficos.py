# -*- coding: utf-8 -*-
"""Diretor.IA - graficos do painel: passar o mouse mostra os valores (tooltip), mas a roda do mouse e o arrastar NAO dao zoom nem deslocam o eixo.
(O grafico nativo do Streamlit, st.line_chart/st.bar_chart, deixa a roda dar zoom: rolar a pagina por cima dele desloca o eixo.)
As funcoes construir_* so montam o grafico (testaveis sem tela); as mostrar_* desenham no Streamlit."""
import altair as alt
import pandas as pd

_COR_PADRAO = ["#4A7BD0", "#F2B134", "#2E9E5B", "#D64545", "#8E6BBF", "#C9CCD8"]


def _quadro(df, nome_x: str = "Categoria") -> pd.DataFrame:
    """Aceita Series (uma serie) ou DataFrame; evita nomes de coluna que colidem com os campos internos (Valor, Serie, eixo X)."""
    if isinstance(df, pd.Series):
        df = df.to_frame(str(df.name) if df.name is not None else "Série única")
    reservados = {"Valor", "Serie", nome_x}
    return df.rename(columns=lambda c: f"{c} (série)" if str(c) in reservados else c)


def _longo(df: pd.DataFrame, nome_x: str = "Categoria") -> pd.DataFrame:
    """Indice vira coluna X; colunas viram series (formato 'longo' do Altair). Valores vazios saem."""
    d = df.copy()
    d.index = d.index.map(str)
    d = d.rename_axis(nome_x).reset_index()
    longo = d.melt(id_vars=nome_x, var_name="Serie", value_name="Valor").dropna(subset=["Valor"])
    posicao = {str(c): i for i, c in enumerate(df.columns)}
    longo["Ordem"] = longo["Serie"].map(lambda c: posicao.get(str(c), 0))
    return longo


def construir_linhas(df: pd.DataFrame, altura: int = 300, nome_x: str = "Período"):
    """Linhas com pontos; df: indice = periodo (texto), colunas = series."""
    df = _quadro(df, nome_x)
    longo = _longo(df, nome_x)
    varias = longo["Serie"].nunique() > 1
    cor = alt.Color("Serie:N", legend=alt.Legend(title=None, orient="bottom") if varias else None, scale=alt.Scale(range=_COR_PADRAO))
    return (
        alt.Chart(longo)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{nome_x}:O", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("Valor:Q", axis=alt.Axis(title=None, format=",.2~f")),
            color=cor,
            tooltip=[alt.Tooltip(f"{nome_x}:O"), alt.Tooltip("Serie:N", title="Série"), alt.Tooltip("Valor:Q", format=",.2f")],
        )
        .properties(height=altura)
    )


def construir_barras(df: pd.DataFrame, altura: int = 300, horizontal: bool = False, empilhar: bool = False, cores: list | None = None):
    """Barras (agrupadas ou empilhadas); df: indice = categoria, colunas = series. A ordem das colunas e' a ordem da pilha/legenda."""
    df = _quadro(df)
    longo = _longo(df)
    ordem_series = [str(c) for c in df.columns]
    cat = alt.X("Categoria:N", sort=None, axis=alt.Axis(labelAngle=0, title=None, labelLimit=180)) if not horizontal else alt.Y("Categoria:N", sort=None, axis=alt.Axis(title=None, labelLimit=180))
    val = alt.Y("Valor:Q", axis=alt.Axis(title=None, tickMinStep=1)) if not horizontal else alt.X("Valor:Q", axis=alt.Axis(title=None, tickMinStep=1))
    if not empilhar:
        val = val.stack(None)
    escala = alt.Scale(domain=ordem_series, range=(cores or _COR_PADRAO)[: len(ordem_series)])
    return (
        alt.Chart(longo)
        .mark_bar()
        .encode(
            cat,
            val,
            color=alt.Color("Serie:N", sort=ordem_series, scale=escala, legend=alt.Legend(title=None, orient="bottom") if len(ordem_series) > 1 else None),
            order=alt.Order("Ordem:Q", sort="ascending"),  # pilha na ordem das colunas (verde, amarelo, vermelho, azul, cinza)
            tooltip=[alt.Tooltip("Categoria:N"), alt.Tooltip("Serie:N", title="Série"), alt.Tooltip("Valor:Q", format=",.2f")],
        )
        .properties(height=altura)
    )


def mostrar_linhas(df: pd.DataFrame, altura: int = 300) -> None:
    import streamlit as st
    st.altair_chart(construir_linhas(df, altura), width="stretch")


def mostrar_barras(df: pd.DataFrame, altura: int = 300, horizontal: bool = False, empilhar: bool = False, cores: list | None = None) -> None:
    import streamlit as st
    st.altair_chart(construir_barras(df, altura, horizontal, empilhar, cores), width="stretch")
