# -*- coding: utf-8 -*-
"""Diretor.IA - registro simples dos reports semanais RECEBIDOS pelo Diretor (o report em si fica no app de quem o escreve).
E' uma AJUDA a gestao, nao uma trava: nenhum campo e' obrigatorio (o que faltar recebe um valor padrao) e o motivo da edicao e' opcional.
Nada se apaga: editar cria uma versao nova (a anterior fica ativo=false); arquivar tira da lista, e da' para restaurar. Validacao pura, testavel sem banco."""
from __future__ import annotations

import datetime as dt

from texto import limpar_texto

STATUS = ("recebido", "em_analise", "tratado")
STATUS_ROTULO = {"recebido": "Recebido", "em_analise": "Em análise", "tratado": "Tratado"}
SEM_NOME = "Não informado"


def segunda_da_semana(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def validar(dados: dict, hoje: dt.date | None = None):
    """Devolve (dados_limpos, avisos). NAO bloqueia: o que faltar ou vier estranho ganha um valor padrao e vira um aviso em linguagem simples
    (a tela mostra o aviso, mas salva do mesmo jeito). A data da semana vira a segunda-feira daquela semana."""
    avisos = []
    hoje = hoje or dt.date.today()
    de_quem = limpar_texto(dados.get("de_quem"), 120)
    if len(de_quem) < 2:                                       # o banco exige 2 a 120 caracteres
        de_quem = SEM_NOME
        avisos.append("Sem o nome de quem enviou: ficou como «Não informado» (dá para corrigir depois).")
    semana = dados.get("semana_de")
    if not isinstance(semana, dt.date):
        semana = hoje
        avisos.append("Sem a semana: usei a semana atual.")
    semana = segunda_da_semana(semana)
    recebido = dados.get("recebido_em")
    if recebido is not None and not isinstance(recebido, dt.date):
        recebido = None
    status = dados.get("status") or "recebido"
    if status not in STATUS:
        status = "recebido"
    resumo = limpar_texto(dados.get("resumo"), 4000) or None
    dific = limpar_texto(dados.get("dificuldades"), 4000) or None
    return {"semana_de": semana, "de_quem": de_quem, "resumo": resumo, "dificuldades": dific, "recebido_em": recebido, "status": status}, avisos


def listar(banco, incluir_antigas: bool = False, limite: int = 300) -> list:
    return banco.consultar(
        """SELECT id, semana_de, de_quem, resumo, dificuldades, recebido_em, status, ativo, substitui_id, criado_por, criado_em, revisado_por, revisado_em, motivo
           FROM diretoria.report_recebido WHERE (%s OR ativo) ORDER BY semana_de DESC, id DESC LIMIT %s""",
        (bool(incluir_antigas), min(int(limite), 1000)))


def listar_arquivados(banco, limite: int = 300) -> list:
    """Registros que a pessoa tirou da lista (ativo=false) e que NAO foram trocados por uma versao nova: esses podem ser restaurados."""
    return banco.consultar(
        """SELECT r.id, r.semana_de, r.de_quem, r.resumo, r.dificuldades, r.recebido_em, r.status, r.motivo, r.revisado_em
           FROM diretoria.report_recebido r
           WHERE NOT r.ativo AND NOT EXISTS (SELECT 1 FROM diretoria.report_recebido x WHERE x.substitui_id = r.id)
           ORDER BY r.semana_de DESC, r.id DESC LIMIT %s""", (min(int(limite), 1000),))


def criar(banco, usuario: str, dados: dict) -> None:
    banco.executar(
        """INSERT INTO diretoria.report_recebido (semana_de, de_quem, resumo, dificuldades, recebido_em, status, criado_por)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (dados["semana_de"], dados["de_quem"], dados["resumo"], dados["dificuldades"], dados["recebido_em"], dados["status"], usuario))


def revisar(banco, usuario: str, id_antigo: int, dados: dict, motivo: str | None = None) -> None:
    """Nova versao + marca a anterior como antiga, na MESMA transacao (ou as duas coisas acontecem, ou nenhuma). Nada e apagado. Motivo opcional."""
    motivo = limpar_texto(motivo, 500) or "Editado"
    banco.executar_varios([
        ("""INSERT INTO diretoria.report_recebido (semana_de, de_quem, resumo, dificuldades, recebido_em, status, criado_por, substitui_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
         (dados["semana_de"], dados["de_quem"], dados["resumo"], dados["dificuldades"], dados["recebido_em"], dados["status"], usuario, int(id_antigo))),
        ("""UPDATE diretoria.report_recebido SET ativo = false, revisado_por = %s, revisado_em = now(), motivo = %s
            WHERE id = %s AND ativo""", (usuario, motivo, int(id_antigo))),
    ])


def arquivar(banco, usuario: str, id_: int, motivo: str | None = None) -> None:
    """Tira da lista (ativo=false). Nao apaga: da' para restaurar."""
    banco.executar(
        "UPDATE diretoria.report_recebido SET ativo = false, revisado_por = %s, revisado_em = now(), motivo = %s WHERE id = %s AND ativo",
        (usuario, limpar_texto(motivo, 500) or "Arquivado", int(id_)))


def restaurar(banco, usuario: str, id_: int) -> None:
    """Volta para a lista um registro arquivado (nao mexe em versoes antigas que ja foram trocadas por uma nova)."""
    banco.executar(
        """UPDATE diretoria.report_recebido SET ativo = true, revisado_por = %s, revisado_em = now(), motivo = 'Restaurado'
           WHERE id = %s AND NOT ativo AND NOT EXISTS (SELECT 1 FROM diretoria.report_recebido x WHERE x.substitui_id = %s)""",
        (usuario, int(id_), int(id_)))
