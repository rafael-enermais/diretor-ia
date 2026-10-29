# -*- coding: utf-8 -*-
"""Diretor.IA - Reports e pendencias: as dificuldades, pendencias, problemas e evolucoes que o Diretor recebe por colaborador (de outros apps ou digitadas aqui),
com classificacao (tipo, urgencia, situacao), nota, vinculo opcional com um indicador/entregavel e historico. E' uma ajuda a gestao, nao uma trava: nenhum campo
e' obrigatorio, tudo e' editavel na propria tabela e nada se apaga (a situacao 'Arquivada' tira da lista). Cada mudanca fica guardada no historico.
O vinculo com indicador so' e' SUGERIDO pelo app; so' vale depois que o usuario confirma."""
import html

import pandas as pd
import streamlit as st

import base
import catalogo
import exportacao
import graficos
import logs_app
import reports
import vinculos
from fuso import agora_br, fmt_br

banco, usuario, papel = base.contexto()
st.title("Reports e pendências")
st.caption("O que os colaboradores relatam (dificuldades, pendências, problemas, evoluções), com urgência e acompanhamento. Nenhum campo é obrigatório e tudo pode ser editado aqui mesmo. Nada é apagado.")

if not reports.instalado(banco):
    st.info("Esta tela ainda não foi ligada no banco. Quem administra o banco precisa rodar o **SQL-04** (tabelas de reports e pendências) e o **SQL-05** (vínculo opcional com indicadores). Depois é só recarregar a página.")
    st.stop()

try:
    itens = reports.listar(banco)
except Exception as exc:                                        # noqa: BLE001
    base.falha(banco, "reports", "listar", exc, usuario)
    itens = []
try:
    CAT = [i for i in catalogo.carregar(banco) if i.get("item_id")]
except Exception:                                               # noqa: BLE001  (sem catalogo a tela funciona, so' sem os vinculos)
    CAT = []
IDS_CAT = {i["item_id"] for i in CAT}

if msg := st.session_state.pop("rep_msg", None):
    st.success(msg)

ROT_URG = {"critica": "🔴 Crítica", "alta": "🟠 Alta", "media": "🟡 Média", "baixa": "⚪ Baixa"}
ROT_SIT = {"nova": "🆕 Nova", "acompanhamento": "👀 Em acompanhamento", "resolvida": "✅ Resolvida", "arquivada": "🗄️ Arquivada"}
ROT_TIPO = reports.TIPOS
INV = {"urgencia": {v: k for k, v in ROT_URG.items()}, "situacao": {v: k for k, v in ROT_SIT.items()}, "tipo": {v: k for k, v in ROT_TIPO.items()}}
RANK_URG = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
COLABORADORES = sorted({i["colaborador"] for i in itens})
CORES_URG = ["#C9CCD8", "#F2B134", "#E8833A", "#D64545"]          # Baixa, Média, Alta, Crítica
SEM_VINC = "—"
OPC_VINC = [SEM_VINC] + [vinculos.rotulo(i["item_id"], CAT) for i in CAT]
OPC_VINC += sorted({vinculos.rotulo(i["vinculo_item_id"], CAT) for i in itens if i.get("vinculo_item_id")} - set(OPC_VINC))      # vinculo antigo de item que saiu do catalogo


def _vinc(rot):
    """'I27 · Contas a pagar' -> 'I27'; vazio ou '—' -> None."""
    return None if rot in (None, "", SEM_VINC) or (not isinstance(rot, str) and pd.isna(rot)) else str(rot).split(" ")[0]


def _vinculo_rotulo(i):
    return vinculos.rotulo(i.get("vinculo_item_id"), CAT) or SEM_VINC


def _campos_atuais(i):
    return {c: i.get(c) for c in reports.CAMPOS}


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
                              "Situação": ROT_SIT[i["situacao"]], "Vínculo": _vinculo_rotulo(i), "Título": i.get("titulo") or "", "Descrição": i.get("descricao") or "",
                              "Nota do Diretor": i.get("nota_diretor") or "", "Origem": i["origem"], "Recebido": fmt_br(i.get("recebido_em"))} for i in vis])
        st.caption("Clique numa célula para editar (urgência, situação, vínculo, nota…). Depois clique em **Salvar alterações**. Para tirar da lista, mude a situação para «Arquivada».")
        ed = st.data_editor(
            orig, key=f"rep_editor_{len(vis)}", hide_index=True, num_rows="fixed", width="stretch", disabled=["Nº", "Origem", "Recebido"],
            column_config={
                "Nº": st.column_config.NumberColumn("Nº", width="small"),
                "Semana": st.column_config.DateColumn("Semana", format="DD/MM/YYYY"),
                "Colaborador": st.column_config.TextColumn("Colaborador", max_chars=120),
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=list(ROT_TIPO.values())),
                "Urgência": st.column_config.SelectboxColumn("Urgência", options=list(ROT_URG.values())),
                "Situação": st.column_config.SelectboxColumn("Situação", options=list(ROT_SIT.values())),
                "Vínculo": st.column_config.SelectboxColumn("Vínculo (opcional)", options=OPC_VINC, help="Indicador (I##) ou entregável (E##) a que este item se refere."),
                "Título": st.column_config.TextColumn("Título", max_chars=200),
                "Descrição": st.column_config.TextColumn("Descrição", max_chars=4000, width="large"),
                "Nota do Diretor": st.column_config.TextColumn("Nota do Diretor", max_chars=4000, width="large"),
            })
        b1, b2 = st.columns([1, 3])
        if b1.button("Salvar alterações", type="primary", key="rep_salvar"):
            por_id = {i["id"]: i for i in itens}
            feitos, avisos_gerais, falhas = 0, [], 0
            for idx in range(len(orig)):
                n = ed.iloc[idx]
                id_ = int(orig.iloc[idx]["Nº"])

                def _d(v):
                    return None if v is None or (not isinstance(v, str) and pd.isna(v)) else (v.date() if isinstance(v, pd.Timestamp) else v)
                dados, avisos = reports.validar({
                    "colaborador": n["Colaborador"], "semana_de": _d(n["Semana"]), "tipo": INV["tipo"].get(n["Tipo"]), "urgencia": INV["urgencia"].get(n["Urgência"]),
                    "situacao": INV["situacao"].get(n["Situação"]), "titulo": n["Título"], "descricao": n["Descrição"], "nota_diretor": n["Nota do Diretor"],
                    "vinculo_item_id": _vinc(n["Vínculo"])}, agora_br().date(), IDS_CAT or None)
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

        # ---- exportar em planilha (os itens que estao na lista, com os filtros acima)
        if b2.button("Preparar planilha (Excel) dos itens desta lista", key="rep_prep_xlsx"):
            try:
                hist = reports.historico_geral(banco, [i["id"] for i in vis])
                filtros = "; ".join(x for x in (("Situação: " + ", ".join(f_sit)) if f_sit else "", ("Urgência: " + ", ".join(f_urg)) if f_urg else "",
                                                ("Tipo: " + ", ".join(f_tipo)) if f_tipo else "", ("Colaborador: " + ", ".join(f_col)) if f_col else "") if x)
                st.session_state["rep_xlsx"] = (exportacao.pendencias_xlsx(vis, hist, CAT, agora_br(), filtros), f"pendencias_{agora_br():%Y-%m-%d_%H%M}.xlsx", len(vis))
                logs_app.registrar(banco, "evento", "reports", "exportar", "Planilha de pendências gerada", usuario=usuario, contexto={"itens": len(vis)})
            except Exception as exc:                            # noqa: BLE001
                base.falha(banco, "reports", "exportar", exc, usuario)
        if st.session_state.get("rep_xlsx"):
            dados_x, nome_x, n_x = st.session_state["rep_xlsx"]
            st.download_button(f"Baixar planilha ({n_x} itens)", data=dados_x, file_name=nome_x, key="rep_baixar_xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.caption("A planilha tem 3 abas: Pendências, Resumo e Histórico. Se mudar os filtros, clique em «Preparar planilha» de novo.")

    # ---- vinculos SUGERIDOS (nunca gravados sem o usuario confirmar)
    pend = [i for i in itens if i["situacao"] in reports.ABERTAS and not i.get("vinculo_item_id")]
    sugestoes = []
    for i in pend:
        s = vinculos.sugerir(" ".join(x for x in (i.get("titulo"), i.get("descricao"), i.get("nota_diretor")) if x), CAT, vinculos.recusados(i.get("vinculo_recusados")), 1)
        if s:
            sugestoes.append((i, s[0]))
    with st.expander(f"Vínculos sugeridos para confirmar ({len(sugestoes)})", expanded=bool(sugestoes)):
        st.caption("O app só **sugere** a que indicador ou entregável um item se refere (pelo código citado ou pelo nome no texto). O vínculo só vale depois que você clica em Confirmar. "
                   "«Não é esse» faz o app parar de sugerir aquele item para aquele relato.")
        if not sugestoes:
            st.caption("Nenhuma sugestão pendente.")
        for i, s in sugestoes[:10]:
            c1, c2, c3 = st.columns([5, 3, 2])
            c1.markdown(f'**Nº {i["id"]}** · {i["colaborador"]} · {(i.get("titulo") or "sem título")[:90]}'.replace("$", "\\$"))
            c2.markdown(f'Sugestão: **{html.escape(vinculos.rotulo(s["item_id"], CAT))}**  \n<small>{html.escape(s["motivo"])} (confiança {s["confianca"]})</small>', unsafe_allow_html=True)
            ok, nao = c3.columns(2)
            if ok.button("Confirmar", key=f"vinc_ok_{i['id']}_{s['item_id']}"):
                try:
                    reports.atualizar(banco, usuario, i["id"], i, {**_campos_atuais(i), "vinculo_item_id": s["item_id"]})
                    logs_app.registrar(banco, "evento", "reports", "vinculo_confirmado", "Vínculo confirmado", usuario=usuario, contexto={"id": i["id"], "vinculo": s["item_id"]})
                    st.session_state["rep_msg"] = f"Item nº {i['id']} vinculado a {vinculos.rotulo(s['item_id'], CAT)}."
                    st.rerun()
                except Exception as exc:                        # noqa: BLE001
                    base.falha(banco, "reports", "confirmar_vinculo", exc, usuario)
            if nao.button("Não é esse", key=f"vinc_no_{i['id']}_{s['item_id']}"):
                try:
                    reports.recusar_vinculo(banco, usuario, i["id"], i.get("vinculo_recusados"), s["item_id"])
                    logs_app.registrar(banco, "evento", "reports", "vinculo_recusado", "Vínculo sugerido recusado", usuario=usuario, contexto={"id": i["id"], "vinculo": s["item_id"]})
                    st.session_state["rep_msg"] = f"Ok: não vou mais sugerir {s['item_id']} para o item nº {i['id']}."
                    st.rerun()
                except Exception as exc:                        # noqa: BLE001
                    base.falha(banco, "reports", "recusar_vinculo", exc, usuario)
        if len(sugestoes) > 10:
            st.caption(f"Mostrando 10 de {len(sugestoes)} sugestões; resolva estas e as próximas aparecem.")

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
        ligados = {}
        for i in reports.abertas(itens):
            if i.get("vinculo_item_id"):
                ligados[vinculos.rotulo(i["vinculo_item_id"], CAT)] = ligados.get(vinculos.rotulo(i["vinculo_item_id"], CAT), 0) + 1
        if ligados:
            st.subheader("Em aberto por indicador/entregável vinculado")
            graficos.mostrar_barras(pd.DataFrame({"Itens em aberto": list(ligados.values())}, index=list(ligados)).sort_values("Itens em aberto", ascending=False),
                                    altura=max(160, 34 * len(ligados) + 60), horizontal=True)

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
        vinc = st.selectbox("Vínculo com indicador/entregável (opcional)", OPC_VINC[1:], index=None, placeholder="Nenhum")
        titulo = st.text_input("Título (uma frase)", max_chars=200)
        descr = st.text_area("Descrição", max_chars=4000, height=110)
        nota = st.text_area("Nota do Diretor (acompanhamento)", max_chars=4000, height=80)
        enviou = st.form_submit_button("Registrar", type="primary")
    if enviou:
        dados, avisos = reports.validar({"colaborador": colab, "semana_de": semana, "tipo": INV["tipo"].get(tipo), "urgencia": INV["urgencia"].get(urg),
                                         "situacao": INV["situacao"].get(sit), "titulo": titulo, "descricao": descr, "nota_diretor": nota,
                                         "vinculo_item_id": _vinc(vinc)}, agora_br().date(), IDS_CAT or None)
        try:
            reports.criar(banco, usuario, dados)
            logs_app.registrar(banco, "evento", "reports", "criar", "Item de report registrado", usuario=usuario, contexto={"semana_de": str(dados["semana_de"]), "tipo": dados["tipo"]})
            st.session_state["rep_msg"] = "Registrado." + "".join(f" {a}" for a in avisos)
            st.rerun()
        except Exception as exc:                                # noqa: BLE001
            base.falha(banco, "reports", "criar", exc, usuario)
