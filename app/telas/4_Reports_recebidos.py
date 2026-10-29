# -*- coding: utf-8 -*-
"""Diretor.IA - Reports recebidos: registro simples (feito pelo Diretor) dos reports semanais que recebeu. O report em si fica no app de quem o escreve.
E' uma ajuda a gestao, nao uma trava: nenhum campo e' obrigatorio, a tabela e' editavel na propria tela e nada se apaga
(editar guarda a versao anterior; arquivar tira da lista e da' para restaurar)."""
import datetime as dt

import pandas as pd
import streamlit as st

import base
import catalogo
import logs_app
import reports
from fuso import agora_br, fmt_br

banco, usuario, papel = base.contexto()
st.title("Reports recebidos")
st.caption("Um registro simples e flexível de quem enviou o report da semana, o resumo e as dificuldades. Nenhum campo é obrigatório e tudo pode ser editado aqui mesmo. O report completo continua no app de quem o escreve.")

try:
    ativos = reports.listar(banco)
except Exception as exc:                                        # noqa: BLE001
    base.falha(banco, "reports", "listar", exc, usuario)
    ativos = []

try:
    itens = catalogo.carregar(banco)
    NOMES = sorted({i["responsavel"] for i in catalogo.entregas(itens) if i.get("nome") == "Report semanal" and i.get("responsavel")})
except Exception:                                               # noqa: BLE001
    NOMES = []

ROTULO_PARA_STATUS = {v: k for k, v in reports.STATUS_ROTULO.items()}
CAMPOS = ["Semana de", "De quem", "Situação", "Recebido em", "Resumo", "Dificuldades"]


def _n(v):
    """Normaliza valor de celula para comparar (vazio = None; Timestamp = date; texto sem espacos nas pontas)."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, pd.Timestamp):
        return v.date()
    if isinstance(v, str):
        return v.strip() or None
    return v


def _linhas(rs):
    return [{"Nº": r["id"], "Semana de": r["semana_de"], "De quem": r["de_quem"], "Situação": reports.STATUS_ROTULO.get(r["status"], r["status"]),
             "Recebido em": r.get("recebido_em"), "Resumo": r.get("resumo") or "", "Dificuldades": r.get("dificuldades") or "", "Arquivar": False} for r in rs]


def _aviso(avisos):
    for a in avisos:
        st.info(a)


if msg := st.session_state.pop("rep_msg", None):
    st.success(msg)

aba_lista, aba_novo = st.tabs(["Registros (editáveis)", "Registrar novo"])

with aba_lista:
    if not ativos:
        st.info("Nenhum report registrado ainda. Use a aba **Registrar novo**.")
    else:
        sit = st.multiselect("Filtrar por situação", list(reports.STATUS_ROTULO.values()), key="rep_filtro")
        linhas = [l for l in _linhas(ativos) if not sit or l["Situação"] in sit]
        orig = pd.DataFrame(linhas)
        st.caption("Clique numa célula para editar. Para tirar um registro da lista, marque **Arquivar** (não apaga; dá para restaurar abaixo). Depois clique em **Salvar alterações**.")
        ed = st.data_editor(
            orig, key=f"rep_editor_{len(linhas)}", hide_index=True, num_rows="fixed", width="stretch", disabled=["Nº"],
            column_config={
                "Nº": st.column_config.NumberColumn("Nº", width="small"),
                "Semana de": st.column_config.DateColumn("Semana de", format="DD/MM/YYYY"),
                "De quem": st.column_config.TextColumn("De quem", max_chars=120),
                "Situação": st.column_config.SelectboxColumn("Situação", options=list(reports.STATUS_ROTULO.values())),
                "Recebido em": st.column_config.DateColumn("Recebido em", format="DD/MM/YYYY"),
                "Resumo": st.column_config.TextColumn("Resumo", max_chars=4000, width="large"),
                "Dificuldades": st.column_config.TextColumn("Dificuldades", max_chars=4000, width="large"),
                "Arquivar": st.column_config.CheckboxColumn("Arquivar", width="small"),
            })
        if st.button("Salvar alterações", type="primary", key="rep_salvar"):
            feitos, avisos_gerais, falhas = 0, [], 0
            for i in range(len(orig)):
                o, n = orig.iloc[i], ed.iloc[i]
                id_ = int(o["Nº"])
                try:
                    if bool(n["Arquivar"]):
                        reports.arquivar(banco, usuario, id_)
                        logs_app.registrar(banco, "evento", "reports", "arquivar", "Report arquivado", usuario=usuario, contexto={"id": id_})
                        feitos += 1
                    elif any(_n(o[c]) != _n(n[c]) for c in CAMPOS):
                        dados, avisos = reports.validar({
                            "semana_de": _n(n["Semana de"]), "de_quem": n["De quem"], "resumo": n["Resumo"], "dificuldades": n["Dificuldades"],
                            "recebido_em": _n(n["Recebido em"]), "status": ROTULO_PARA_STATUS.get(n["Situação"], "recebido")}, agora_br().date())
                        reports.revisar(banco, usuario, id_, dados, "Editado na tabela")
                        logs_app.registrar(banco, "evento", "reports", "revisar", "Report editado (nova versão)", usuario=usuario, contexto={"id_anterior": id_})
                        avisos_gerais += avisos
                        feitos += 1
                except Exception as exc:                        # noqa: BLE001
                    falhas += 1
                    base.falha(banco, "reports", "salvar_tabela", exc, usuario)
            if feitos and not falhas:
                st.session_state["rep_msg"] = f"{feitos} registro(s) atualizado(s)." + ("".join(f" {a}" for a in dict.fromkeys(avisos_gerais)))
                st.rerun()
            elif not feitos and not falhas:
                st.info("Nada foi alterado.")

    with st.expander("Arquivados e versões antigas"):
        try:
            arq = reports.listar_arquivados(banco)
            todos = [r for r in reports.listar(banco, incluir_antigas=True) if not r["ativo"]]
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "listar_antigas", exc, usuario)
            arq, todos = [], []
        if arq:
            st.markdown("**Arquivados** (você pode restaurar)")
            rot = {f'{r["semana_de"]:%d/%m/%Y} · {r["de_quem"]} (nº {r["id"]})': r for r in arq}
            esc = st.selectbox("Registro arquivado", list(rot), key="rep_arq_sel")
            if st.button("Restaurar para a lista", key="rep_restaurar"):
                try:
                    reports.restaurar(banco, usuario, rot[esc]["id"])
                    logs_app.registrar(banco, "evento", "reports", "restaurar", "Report restaurado", usuario=usuario, contexto={"id": rot[esc]["id"]})
                    st.session_state["rep_msg"] = "Registro restaurado."
                    st.rerun()
                except Exception as exc:                        # noqa: BLE001
                    base.falha(banco, "reports", "restaurar", exc, usuario)
        else:
            st.caption("Nenhum registro arquivado.")
        ids_arq = {r["id"] for r in arq}
        antigas = [r for r in todos if r["id"] not in ids_arq]
        if antigas:
            st.markdown("**Versões antigas** (guardadas quando você edita)")
            d2 = pd.DataFrame([{"Semana de": r["semana_de"].strftime("%d/%m/%Y"), "De quem": r["de_quem"], "Situação": reports.STATUS_ROTULO.get(r["status"], r["status"]),
                                "Resumo": r.get("resumo") or "—", "Dificuldades": r.get("dificuldades") or "—", "Substituída em": fmt_br(r.get("revisado_em"))} for r in antigas])
            st.dataframe(d2, hide_index=True, width="stretch")

with aba_novo:
    st.caption("Preencha só o que quiser. Se deixar algo em branco, o app registra do mesmo jeito (você edita depois na tabela).")
    with st.form("rep_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        semana = c1.date_input("Semana do report (qualquer dia da semana)", value=agora_br().date(), format="DD/MM/YYYY")
        recebido = c2.date_input("Recebido em", value=agora_br().date(), format="DD/MM/YYYY")
        de_quem = st.selectbox("De quem", NOMES, index=None, accept_new_options=True, placeholder="Escolha ou digite um nome")
        resumo = st.text_area("Resumo do report", max_chars=4000, height=120)
        dific = st.text_area("Dificuldades relatadas", max_chars=4000, height=100)
        status = st.selectbox("Situação", list(reports.STATUS_ROTULO), format_func=lambda k: reports.STATUS_ROTULO[k])
        enviou = st.form_submit_button("Registrar", type="primary")
    if enviou:
        dados, avisos = reports.validar({"semana_de": semana, "de_quem": de_quem, "resumo": resumo, "dificuldades": dific, "recebido_em": recebido, "status": status}, agora_br().date())
        try:
            reports.criar(banco, usuario, dados)
            logs_app.registrar(banco, "evento", "reports", "criar", "Report recebido registrado", usuario=usuario, contexto={"semana_de": str(dados["semana_de"])})
            st.session_state["rep_msg"] = "Registrado." + "".join(f" {a}" for a in avisos)
            st.rerun()
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "criar", exc, usuario)
