# -*- coding: utf-8 -*-
"""Diretor.IA - Reports recebidos: registro simples (feito pelo Diretor) dos reports semanais que recebeu. O report em si fica no app de quem o escreve.
Nada se apaga: editar cria uma versao nova e a anterior fica guardada (com o motivo)."""
import datetime as dt

import pandas as pd
import streamlit as st

import base
import logs_app
import reports
from fuso import agora_br, fmt_br

banco, usuario, papel = base.contexto()
st.title("Reports recebidos")
st.caption("Um registro simples de quem enviou o report da semana, o resumo e as dificuldades. O report completo continua no app de quem o escreve.")

try:
    ativos = reports.listar(banco)
except Exception as exc:                                        # noqa: BLE001
    base.falha(banco, "reports", "listar", exc, usuario)
    ativos = []


def _linhas(rs):
    return [{"Semana de": r["semana_de"].strftime("%d/%m/%Y") if r.get("semana_de") else "—", "De quem": r["de_quem"],
             "Situação": reports.STATUS_ROTULO.get(r["status"], r["status"]), "Recebido em": fmt_br(r.get("recebido_em")),
             "Resumo": r.get("resumo") or "—", "Dificuldades": r.get("dificuldades") or "—", "Registro": fmt_br(r.get("criado_em"))} for r in rs]


aba_lista, aba_novo, aba_editar = st.tabs(["Registros", "Registrar novo", "Corrigir um registro"])

with aba_lista:
    if not ativos:
        st.info("Nenhum report registrado ainda. Use a aba **Registrar novo**.")
    else:
        sit = st.multiselect("Situação", list(reports.STATUS_ROTULO.values()), key="rep_filtro")
        df = pd.DataFrame(_linhas(ativos))
        if sit:
            df = df[df["Situação"].isin(sit)]
        st.dataframe(df, hide_index=True, width="stretch")
    if st.toggle("Mostrar também versões antigas (corrigidas)", key="rep_antigas"):
        try:
            todos = [r for r in reports.listar(banco, incluir_antigas=True) if not r["ativo"]]
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "listar_antigas", exc, usuario)
            todos = []
        if todos:
            d2 = pd.DataFrame(_linhas(todos))
            d2["Motivo da correção"] = [r.get("motivo") or "—" for r in todos]
            st.dataframe(d2, hide_index=True, width="stretch")
        else:
            st.caption("Nenhuma versão antiga.")

with aba_novo:
    with st.form("rep_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        semana = c1.date_input("Semana do report (qualquer dia da semana)", value=agora_br().date(), format="DD/MM/YYYY")
        recebido = c2.date_input("Recebido em", value=agora_br().date(), format="DD/MM/YYYY")
        de_quem = st.text_input("De quem", max_chars=120)
        resumo = st.text_area("Resumo do report", max_chars=4000, height=120)
        dific = st.text_area("Dificuldades relatadas", max_chars=4000, height=100)
        status = st.selectbox("Situação", list(reports.STATUS_ROTULO), format_func=lambda k: reports.STATUS_ROTULO[k])
        enviou = st.form_submit_button("Registrar", type="primary")
    if enviou:
        dados, erros = reports.validar({"semana_de": semana, "de_quem": de_quem, "resumo": resumo, "dificuldades": dific, "recebido_em": recebido, "status": status})
        if erros:
            for e in erros:
                st.error(e)
        else:
            try:
                reports.criar(banco, usuario, dados)
                logs_app.registrar(banco, "evento", "reports", "criar", "Report recebido registrado", usuario=usuario, contexto={"semana_de": str(dados["semana_de"])})
                st.success("Registrado.")
                st.rerun()
            except Exception as exc:                            # noqa: BLE001
                base.falha(banco, "reports", "criar", exc, usuario)

with aba_editar:
    if not ativos:
        st.info("Nada para corrigir ainda.")
    else:
        rot = {f'{r["semana_de"]:%d/%m/%Y} · {r["de_quem"]} (nº {r["id"]})': r for r in ativos}
        r = rot[st.selectbox("Registro", list(rot), key="rep_sel")]
        with st.form(f'rep_edit_{r["id"]}'):
            c1, c2 = st.columns(2)
            semana = c1.date_input("Semana do report", value=r["semana_de"], format="DD/MM/YYYY")
            recebido = c2.date_input("Recebido em", value=r["recebido_em"] or r["semana_de"], format="DD/MM/YYYY")
            de_quem = st.text_input("De quem", value=r["de_quem"], max_chars=120)
            resumo = st.text_area("Resumo do report", value=r.get("resumo") or "", max_chars=4000, height=120)
            dific = st.text_area("Dificuldades relatadas", value=r.get("dificuldades") or "", max_chars=4000, height=100)
            status = st.selectbox("Situação", list(reports.STATUS_ROTULO), index=list(reports.STATUS_ROTULO).index(r["status"]),
                                  format_func=lambda k: reports.STATUS_ROTULO[k])
            motivo = st.text_input("Motivo da correção (obrigatório)", max_chars=500)
            enviou = st.form_submit_button("Salvar como nova versão", type="primary")
        st.caption("A versão anterior não é apagada: fica guardada como «antiga», com o motivo.")
        if enviou:
            dados, erros = reports.validar({"semana_de": semana, "de_quem": de_quem, "resumo": resumo, "dificuldades": dific, "recebido_em": recebido, "status": status})
            if len((motivo or "").strip()) < 3:
                erros.append("Informe o motivo da correção.")
            if erros:
                for e in erros:
                    st.error(e)
            else:
                try:
                    reports.revisar(banco, usuario, r["id"], dados, motivo)
                    logs_app.registrar(banco, "evento", "reports", "revisar", "Report corrigido (nova versão)", usuario=usuario, contexto={"id_anterior": r["id"]})
                    st.success("Nova versão salva.")
                    st.rerun()
                except Exception as exc:                        # noqa: BLE001
                    base.falha(banco, "reports", "revisar", exc, usuario)
