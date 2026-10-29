# -*- coding: utf-8 -*-
"""Diretor.IA - Reports e pendencias: as dificuldades, pendencias, problemas e evolucoes que o Diretor recebe por colaborador (de outros apps ou digitadas aqui),
com classificacao (tipo, urgencia, situacao), nota e historico. E' uma ajuda a gestao, nao uma trava: nenhum campo e' obrigatorio, tudo e' editavel na propria
tabela e nada se apaga (a situacao 'Arquivada' tira da lista). Cada mudanca fica guardada no historico."""
import pandas as pd
import streamlit as st

import base
import graficos
import logs_app
import reports
from fuso import agora_br, fmt_br

banco, usuario, papel = base.contexto()
st.title("Reports e pendências")
st.caption("O que os colaboradores relatam (dificuldades, pendências, problemas, evoluções), com urgência e acompanhamento. Nenhum campo é obrigatório e tudo pode ser editado aqui mesmo. Nada é apagado.")

if not reports.instalado(banco):
    st.info("Esta tela ainda não foi ligada no banco. Quem administra o banco precisa rodar o **SQL-04** (tabelas de reports e pendências). Depois é só recarregar a página.")
    st.stop()

try:
    itens = reports.listar(banco)
except Exception as exc:                                        # noqa: BLE001
    base.falha(banco, "reports", "listar", exc, usuario)
    itens = []

if msg := st.session_state.pop("rep_msg", None):
    st.success(msg)

ROT_URG = {"critica": "🔴 Crítica", "alta": "🟠 Alta", "media": "🟡 Média", "baixa": "⚪ Baixa"}
ROT_SIT = {"nova": "🆕 Nova", "acompanhamento": "👀 Em acompanhamento", "resolvida": "✅ Resolvida", "arquivada": "🗄️ Arquivada"}
ROT_TIPO = reports.TIPOS
INV = {"urgencia": {v: k for k, v in ROT_URG.items()}, "situacao": {v: k for k, v in ROT_SIT.items()}, "tipo": {v: k for k, v in ROT_TIPO.items()}}
RANK_URG = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
COLABORADORES = sorted({i["colaborador"] for i in itens})
CORES_URG = ["#C9CCD8", "#F2B134", "#E8833A", "#D64545"]          # Baixa, Média, Alta, Crítica

aba_acomp, aba_evol, aba_hist, aba_novo = st.tabs(["Acompanhamento", "Evolução", "Histórico de um item", "Registrar novo"])

with aba_acomp:
    k = reports.kpis(itens, agora_br().date())
    c = st.columns(5)
    c[0].metric("Em aberto", k["abertas"])
    c[1].metric("Urgentes (alta/crítica)", k["urgentes"])
    c[2].metric("Críticas", k["criticas"])
    c[3].metric("Resolvidas (30 dias)", k["resolvidas_30d"])
    c[4].metric("Colaboradores com item aberto", k["colaboradores_com_aberta"])

    f = st.columns(4)
    f_sit = f[0].multiselect("Situação", list(ROT_SIT.values()), default=[ROT_SIT["nova"], ROT_SIT["acompanhamento"]], key="rep_f_sit")
    f_urg = f[1].multiselect("Urgência", list(ROT_URG.values()), key="rep_f_urg")
    f_tipo = f[2].multiselect("Tipo", list(ROT_TIPO.values()), key="rep_f_tipo")
    f_col = f[3].multiselect("Colaborador", COLABORADORES, key="rep_f_col")

    def _passa(i):
        return ((not f_sit or ROT_SIT[i["situacao"]] in f_sit) and (not f_urg or ROT_URG[i["urgencia"]] in f_urg)
                and (not f_tipo or ROT_TIPO[i["tipo"]] in f_tipo) and (not f_col or i["colaborador"] in f_col))

    vis = sorted([i for i in itens if _passa(i)], key=lambda i: (RANK_URG[i["urgencia"]], -i["semana_de"].toordinal(), -i["id"]))
    if not itens:
        st.info("Nenhum item ainda. Eles chegam dos outros apps, ou use a aba **Registrar novo**.")
    elif not vis:
        st.info("Nenhum item com esses filtros.")
    else:
        orig = pd.DataFrame([{"Nº": i["id"], "Semana": i["semana_de"], "Colaborador": i["colaborador"], "Tipo": ROT_TIPO[i["tipo"]], "Urgência": ROT_URG[i["urgencia"]],
                              "Situação": ROT_SIT[i["situacao"]], "Título": i.get("titulo") or "", "Descrição": i.get("descricao") or "",
                              "Nota do Diretor": i.get("nota_diretor") or "", "Origem": i["origem"], "Recebido": fmt_br(i.get("recebido_em"))} for i in vis])
        st.caption("Clique numa célula para editar (urgência, situação, nota…). Depois clique em **Salvar alterações**. Para tirar da lista, mude a situação para «Arquivada».")
        ed = st.data_editor(
            orig, key=f"rep_editor_{len(vis)}", hide_index=True, num_rows="fixed", width="stretch", disabled=["Nº", "Origem", "Recebido"],
            column_config={
                "Nº": st.column_config.NumberColumn("Nº", width="small"),
                "Semana": st.column_config.DateColumn("Semana", format="DD/MM/YYYY"),
                "Colaborador": st.column_config.TextColumn("Colaborador", max_chars=120),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=list(ROT_TIPO.values())),
                "Urgência": st.column_config.SelectboxColumn("Urgência", options=list(ROT_URG.values())),
                "Situação": st.column_config.SelectboxColumn("Situação", options=list(ROT_SIT.values())),
                "Título": st.column_config.TextColumn("Título", max_chars=200),
                "Descrição": st.column_config.TextColumn("Descrição", max_chars=4000, width="large"),
                "Nota do Diretor": st.column_config.TextColumn("Nota do Diretor", max_chars=4000, width="large"),
            })
        if st.button("Salvar alterações", type="primary", key="rep_salvar"):
            por_id = {i["id"]: i for i in itens}
            feitos, avisos_gerais, falhas = 0, [], 0
            for idx in range(len(orig)):
                n = ed.iloc[idx]
                id_ = int(orig.iloc[idx]["Nº"])

                def _d(v):
                    return None if v is None or (not isinstance(v, str) and pd.isna(v)) else (v.date() if isinstance(v, pd.Timestamp) else v)
                dados, avisos = reports.validar({
                    "colaborador": n["Colaborador"], "semana_de": _d(n["Semana"]), "tipo": INV["tipo"].get(n["Tipo"]), "urgencia": INV["urgencia"].get(n["Urgência"]),
                    "situacao": INV["situacao"].get(n["Situação"]), "titulo": n["Título"], "descricao": n["Descrição"], "nota_diretor": n["Nota do Diretor"]}, agora_br().date())
                try:
                    mudou = reports.atualizar(banco, usuario, id_, por_id[id_], dados)
                    if mudou:
                        logs_app.registrar(banco, "evento", "reports", "atualizar", "Item de report atualizado", usuario=usuario, contexto={"id": id_, "campos": mudou})
                        feitos += 1
                        avisos_gerais += avisos
                except Exception as exc:                        # noqa: BLE001
                    falhas += 1
                    base.falha(banco, "reports", "salvar_tabela", exc, usuario)
            if feitos and not falhas:
                st.session_state["rep_msg"] = f"{feitos} item(ns) atualizado(s)." + "".join(f" {a}" for a in dict.fromkeys(avisos_gerais))
                st.rerun()
            elif not feitos and not falhas:
                st.info("Nada foi alterado.")

with aba_evol:
    if not itens:
        st.info("Quando houver itens, os gráficos de evolução aparecem aqui.")
    else:
        dm = k["dias_medios_para_resolver"]
        st.metric("Tempo médio para resolver", "—" if dm is None else f"{dm:.1f} dias".replace(".", ","), help="Da data de recebimento até marcar como Resolvida.")
        st.subheader("Novos × resolvidos por semana")
        nr = reports.novos_x_resolvidos(itens)
        if len(nr):
            graficos.mostrar_linhas(nr, altura=260)
        st.subheader("Itens por semana, por tipo")
        ss = reports.serie_semanal(itens)
        if len(ss):
            graficos.mostrar_barras(ss, altura=280, empilhar=True)
        st.subheader("Em aberto por colaborador, por urgência")
        ac = reports.abertas_por_colaborador(itens)
        if len(ac):
            graficos.mostrar_barras(ac, altura=max(160, 34 * len(ac) + 60), horizontal=True, empilhar=True, cores=CORES_URG)
        else:
            st.caption("Nenhum item em aberto.")

with aba_hist:
    if not itens:
        st.info("Nenhum item ainda.")
    else:
        rot = {f'nº {i["id"]} · {i["colaborador"]} · {(i.get("titulo") or "sem título")[:50]}': i for i in itens}
        esc = rot[st.selectbox("Item", list(rot), key="rep_hist_sel")]
        try:
            h = reports.historico(banco, esc["id"])
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "historico", exc, usuario)
            h = []
        if h:
            st.dataframe(pd.DataFrame([{"Quando": fmt_br(x["em"]), "Quem": x["por"], "O que mudou": reports.ROTULO_CAMPO.get(x["campo"], x["campo"]),
                                        "De": x.get("de") or "—", "Para": x.get("para") or "—"} for x in h]), hide_index=True, width="stretch")
        else:
            st.caption("Sem mudanças registradas.")

with aba_novo:
    st.caption("Preencha só o que quiser. O que ficar em branco é registrado do mesmo jeito (você ajusta depois na tabela).")
    with st.form("rep_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        semana = c1.date_input("Semana do item (qualquer dia da semana)", value=agora_br().date(), format="DD/MM/YYYY")
        colab = c2.selectbox("Colaborador", COLABORADORES, index=None, accept_new_options=True, placeholder="Escolha ou digite um nome")
        c3, c4, c5 = st.columns(3)
        tipo = c3.selectbox("Tipo", list(ROT_TIPO.values()))
        urg = c4.selectbox("Urgência", list(ROT_URG.values()), index=list(ROT_URG).index("media"))
        sit = c5.selectbox("Situação", list(ROT_SIT.values()))
        titulo = st.text_input("Título (uma frase)", max_chars=200)
        descr = st.text_area("Descrição", max_chars=4000, height=110)
        nota = st.text_area("Nota do Diretor (acompanhamento)", max_chars=4000, height=80)
        enviou = st.form_submit_button("Registrar", type="primary")
    if enviou:
        dados, avisos = reports.validar({"colaborador": colab, "semana_de": semana, "tipo": INV["tipo"].get(tipo), "urgencia": INV["urgencia"].get(urg),
                                         "situacao": INV["situacao"].get(sit), "titulo": titulo, "descricao": descr, "nota_diretor": nota}, agora_br().date())
        try:
            reports.criar(banco, usuario, dados)
            logs_app.registrar(banco, "evento", "reports", "criar", "Item de report registrado", usuario=usuario, contexto={"semana_de": str(dados["semana_de"]), "tipo": dados["tipo"]})
            st.session_state["rep_msg"] = "Registrado." + "".join(f" {a}" for a in avisos)
            st.rerun()
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "criar", exc, usuario)
