# -*- coding: utf-8 -*-
"""Diretor.IA - REPORTS E PENDENCIAS: os itens (dificuldade, pendencia, problema, evolucao) que o Diretor recebe por colaborador, de outros apps ou digitados aqui.
E' uma AJUDA a gestao, nao uma trava: nenhum campo e' obrigatorio (o que faltar recebe valor padrao), tudo e' editavel e nada se apaga
('arquivada' tira da lista). Cada mudanca fica no historico (de -> para). Calculos puros (KPIs, series) testaveis sem banco/tela."""
from __future__ import annotations

import datetime as dt

from texto import limpar_texto

TIPOS = {"dificuldade": "Dificuldade", "pendencia": "Pendência", "problema": "Problema", "evolucao": "Evolução", "outro": "Outro"}
URGENCIAS = {"baixa": "Baixa", "media": "Média", "alta": "Alta", "critica": "Crítica"}
SITUACOES = {"nova": "Nova", "acompanhamento": "Em acompanhamento", "resolvida": "Resolvida", "arquivada": "Arquivada"}
ABERTAS = ("nova", "acompanhamento")
SEM_NOME = "Não informado"
# campos que o Diretor pode editar na tabela (ordem = ordem do historico)
CAMPOS = ("colaborador", "semana_de", "tipo", "urgencia", "situacao", "titulo", "descricao", "nota_diretor")
ROTULO_CAMPO = {"colaborador": "Colaborador", "semana_de": "Semana", "tipo": "Tipo", "urgencia": "Urgência", "situacao": "Situação",
                "titulo": "Título", "descricao": "Descrição", "nota_diretor": "Nota do Diretor", "criado": "Criado", "conteudo_atualizado": "Conteúdo atualizado pelo app"}


def segunda_da_semana(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def instalado(banco) -> bool:
    """O SQL-04 ja foi rodado? (as 2 tabelas existem). Erro de banco => False (a tela explica, nao quebra)."""
    try:
        r = banco.consultar("SELECT to_regclass('diretoria.report_item') IS NOT NULL AS a, to_regclass('diretoria.report_item_historico') IS NOT NULL AS b")
        return bool(r and r[0]["a"] and r[0]["b"])
    except Exception:                                           # noqa: BLE001
        return False


def validar(dados: dict, hoje: dt.date | None = None):
    """Devolve (dados_limpos, avisos). NAO bloqueia: o que faltar ou vier estranho ganha valor padrao e vira um aviso simples (a tela salva do mesmo jeito)."""
    avisos = []
    hoje = hoje or dt.date.today()
    colab = limpar_texto(dados.get("colaborador"), 120)
    if len(colab) < 2:                                          # o banco exige 2 a 120 caracteres
        colab = SEM_NOME
        avisos.append("Sem o nome do colaborador: ficou como «Não informado» (dá para corrigir depois).")
    semana = dados.get("semana_de")
    if not isinstance(semana, dt.date):
        semana = hoje
        avisos.append("Sem a semana: usei a semana atual.")
    semana = segunda_da_semana(semana)
    tipo = dados.get("tipo") if dados.get("tipo") in TIPOS else "dificuldade"
    urg = dados.get("urgencia") if dados.get("urgencia") in URGENCIAS else "media"
    sit = dados.get("situacao") if dados.get("situacao") in SITUACOES else "nova"
    return {"colaborador": colab, "semana_de": semana, "tipo": tipo, "urgencia": urg, "situacao": sit,
            "titulo": limpar_texto(dados.get("titulo"), 200) or None, "descricao": limpar_texto(dados.get("descricao"), 4000) or None,
            "nota_diretor": limpar_texto(dados.get("nota_diretor"), 4000) or None}, avisos


_SQL_LISTAR = """SELECT id, origem, id_externo, colaborador, semana_de, tipo, urgencia, situacao, titulo, descricao, nota_diretor,
                        recebido_em, resolvido_em, criado_por, atualizado_em, atualizado_por
                 FROM diretoria.report_item ORDER BY semana_de DESC, id DESC LIMIT %s"""


def listar(banco, limite: int = 2000) -> list:
    return banco.consultar(_SQL_LISTAR, (min(int(limite), 5000),))


def historico(banco, item_id: int, limite: int = 200) -> list:
    return banco.consultar("SELECT em, por, campo, de, para FROM diretoria.report_item_historico WHERE item_id = %s ORDER BY id DESC LIMIT %s",
                           (int(item_id), min(int(limite), 1000)))


def criar(banco, usuario: str, dados: dict) -> None:
    """Item novo + linha 'criado' no historico, em UM comando (ou tudo ou nada)."""
    banco.executar(
        """WITH n AS (
               INSERT INTO diretoria.report_item (origem, colaborador, semana_de, tipo, urgencia, situacao, titulo, descricao, nota_diretor, criado_por, resolvido_em)
               VALUES ('manual', %s, %s, %s, %s, %s, %s, %s, %s, %s, CASE WHEN %s = 'resolvida' THEN now() END) RETURNING id)
           INSERT INTO diretoria.report_item_historico (item_id, por, campo, para) SELECT id, %s, 'criado', %s FROM n""",
        (dados["colaborador"], dados["semana_de"], dados["tipo"], dados["urgencia"], dados["situacao"], dados["titulo"], dados["descricao"], dados["nota_diretor"],
         usuario, dados["situacao"], usuario, f'{dados["tipo"]} / {dados["urgencia"]}'))


def _txt(v, limite: int = 300):
    if v is None:
        return None
    if isinstance(v, dt.date):
        return v.strftime("%d/%m/%Y")
    s = str(TIPOS.get(v) or URGENCIAS.get(v) or SITUACOES.get(v) or v)
    return s[:limite]


def diferencas(antigo: dict, novo: dict) -> list:
    """[(campo, de, para)] so' dos campos editaveis que mudaram (vazio e None contam como igual)."""
    def n(v):
        return None if v is None or (isinstance(v, str) and not v.strip()) else v
    return [(c, n(antigo.get(c)), n(novo.get(c))) for c in CAMPOS if n(antigo.get(c)) != n(novo.get(c))]


def atualizar(banco, usuario: str, item_id: int, antigo: dict, novo: dict) -> int:
    """Grava so' o que mudou + uma linha de historico por campo, na MESMA transacao. Devolve quantos campos mudaram (0 = nada a fazer). Nada e' apagado."""
    difs = diferencas(antigo, novo)
    if not difs:
        return 0
    sets = ", ".join(f"{c} = %s" for c, _, _ in difs)           # nomes vem da lista fixa CAMPOS (nunca do usuario)
    params = [p for _, _, p in difs]
    resolvido = ""
    nova_sit = novo.get("situacao")
    if any(c == "situacao" for c, _, _ in difs):
        if nova_sit == "resolvida":
            resolvido = ", resolvido_em = COALESCE(resolvido_em, now())"
        elif nova_sit in ABERTAS:
            resolvido = ", resolvido_em = NULL"
    stmts = [(f"UPDATE diretoria.report_item SET {sets}, atualizado_em = now(), atualizado_por = %s{resolvido} WHERE id = %s", (*params, usuario, int(item_id)))]
    for c, de, para in difs:
        stmts.append(("INSERT INTO diretoria.report_item_historico (item_id, por, campo, de, para) VALUES (%s,%s,%s,%s,%s)", (int(item_id), usuario, c, _txt(de), _txt(para))))
    banco.executar_varios(stmts)
    return len(difs)


# ---------------------------------------------------------------- calculos para os paineis (puros)

def abertas(itens: list) -> list:
    return [i for i in itens if i.get("situacao") in ABERTAS]


def _data(v):
    return v.date() if isinstance(v, dt.datetime) else v


def kpis(itens: list, hoje: dt.date | None = None) -> dict:
    hoje = hoje or dt.date.today()
    ab = abertas(itens)
    res30 = [i for i in itens if i.get("situacao") == "resolvida" and i.get("resolvido_em") and (hoje - _data(i["resolvido_em"])).days <= 30]
    dias = [max((_data(i["resolvido_em"]) - _data(i["recebido_em"])).days, 0) for i in itens if i.get("resolvido_em") and i.get("recebido_em")]
    return {"abertas": len(ab), "urgentes": sum(1 for i in ab if i.get("urgencia") in ("alta", "critica")), "criticas": sum(1 for i in ab if i.get("urgencia") == "critica"),
            "resolvidas_30d": len(res30), "colaboradores_com_aberta": len({i["colaborador"] for i in ab}),
            "dias_medios_para_resolver": round(sum(dias) / len(dias), 1) if dias else None}


def serie_semanal(itens: list):
    """DataFrame: indice = semana (dd/mm/aaaa, em ordem), colunas = tipos; valor = quantos itens chegaram naquela semana."""
    import pandas as pd
    if not itens:
        return pd.DataFrame()
    df = pd.DataFrame([{"semana": i["semana_de"], "tipo": TIPOS.get(i["tipo"], i["tipo"])} for i in itens])
    t = df.groupby(["semana", "tipo"]).size().unstack(fill_value=0).sort_index()
    ordem = [TIPOS[k] for k in TIPOS if TIPOS[k] in t.columns]
    t = t[ordem]
    t.index = [d.strftime("%d/%m/%Y") for d in t.index]
    return t


def novos_x_resolvidos(itens: list):
    """DataFrame: indice = semana (segunda), colunas 'Novos' (por semana do item) e 'Resolvidos' (pela semana em que foram resolvidos)."""
    import pandas as pd
    from collections import Counter
    novos = Counter(i["semana_de"] for i in itens)
    res = Counter(segunda_da_semana(_data(i["resolvido_em"])) for i in itens if i.get("resolvido_em"))
    sem = sorted(set(novos) | set(res))
    if not sem:
        return pd.DataFrame()
    return pd.DataFrame({"Novos": [novos.get(s, 0) for s in sem], "Resolvidos": [res.get(s, 0) for s in sem]}, index=[s.strftime("%d/%m/%Y") for s in sem])


def abertas_por_colaborador(itens: list):
    """DataFrame: indice = colaborador (so' os que tem item aberto, mais itens primeiro), colunas = urgencias (Baixa..Crítica)."""
    import pandas as pd
    ab = abertas(itens)
    if not ab:
        return pd.DataFrame()
    df = pd.DataFrame([{"colab": i["colaborador"], "urg": URGENCIAS.get(i["urgencia"], i["urgencia"])} for i in ab])
    t = df.groupby(["colab", "urg"]).size().unstack(fill_value=0)
    for u in URGENCIAS.values():
        if u not in t.columns:
            t[u] = 0
    t = t[list(URGENCIAS.values())]
    return t.loc[t.sum(axis=1).sort_values(ascending=False).index]
