# -*- coding: utf-8 -*-
"""Diretor.IA - registro simples dos reports semanais RECEBIDOS pelo Diretor (o report em si fica no app de quem o escreve).
Nada se apaga: editar cria uma versao nova (a anterior fica ativo=false, com motivo). Validacao pura, testavel sem banco."""
from __future__ import annotations

import datetime as dt

from texto import limpar_texto

STATUS = ("recebido", "em_analise", "tratado")
STATUS_ROTULO = {"recebido": "Recebido", "em_analise": "Em análise", "tratado": "Tratado"}


def segunda_da_semana(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def validar(dados: dict):
    """Devolve (dados_limpos, erros). Erros em linguagem simples. A data da semana vira a segunda-feira daquela semana."""
    erros = []
    de_quem = limpar_texto(dados.get("de_quem"), 120)
    if not (2 <= len(de_quem) <= 120):
        erros.append("Informe de quem é o report (2 a 120 caracteres).")
    semana = dados.get("semana_de")
    if not isinstance(semana, dt.date):
        erros.append("Informe a semana do report.")
        semana = None
    else:
        semana = segunda_da_semana(semana)
    recebido = dados.get("recebido_em")
    if recebido is not None and not isinstance(recebido, dt.date):
        erros.append("A data de recebimento é inválida.")
        recebido = None
    status = dados.get("status") or "recebido"
    if status not in STATUS:
        erros.append("Situação inválida.")
    resumo = limpar_texto(dados.get("resumo"), 4000) or None
    dific = limpar_texto(dados.get("dificuldades"), 4000) or None
    return {"semana_de": semana, "de_quem": de_quem, "resumo": resumo, "dificuldades": dific, "recebido_em": recebido, "status": status}, erros


def listar(banco, incluir_antigas: bool = False, limite: int = 300) -> list:
    return banco.consultar(
        """SELECT id, semana_de, de_quem, resumo, dificuldades, recebido_em, status, ativo, substitui_id, criado_por, criado_em, revisado_por, revisado_em, motivo
           FROM diretoria.report_recebido WHERE (%s OR ativo) ORDER BY semana_de DESC, id DESC LIMIT %s""",
        (bool(incluir_antigas), min(int(limite), 1000)))


def criar(banco, usuario: str, dados: dict) -> None:
    banco.executar(
        """INSERT INTO diretoria.report_recebido (semana_de, de_quem, resumo, dificuldades, recebido_em, status, criado_por)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (dados["semana_de"], dados["de_quem"], dados["resumo"], dados["dificuldades"], dados["recebido_em"], dados["status"], usuario))


def revisar(banco, usuario: str, id_antigo: int, dados: dict, motivo: str) -> None:
    """Nova versao + marca a anterior como antiga, na MESMA transacao (ou as duas coisas acontecem, ou nenhuma). Nada e apagado."""
    motivo = limpar_texto(motivo, 500)
    if len(motivo) < 3:
        raise ValueError("Informe o motivo da alteração.")
    banco.executar_varios([
        ("""INSERT INTO diretoria.report_recebido (semana_de, de_quem, resumo, dificuldades, recebido_em, status, criado_por, substitui_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
         (dados["semana_de"], dados["de_quem"], dados["resumo"], dados["dificuldades"], dados["recebido_em"], dados["status"], usuario, int(id_antigo))),
        ("""UPDATE diretoria.report_recebido SET ativo = false, revisado_por = %s, revisado_em = now(), motivo = %s
            WHERE id = %s AND ativo""", (usuario, motivo, int(id_antigo))),
    ])
