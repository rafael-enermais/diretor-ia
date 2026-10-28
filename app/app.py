# -*- coding: utf-8 -*-
"""Diretor.IA - ponto de entrada (Streamlit). Fluxo: login (Supabase) -> acesso fail-closed (diretoria.acesso) -> menu.
As telas ficam em app/telas/ (fora de uma pasta chamada "pages") para o menu so existir DEPOIS do login e da checagem de acesso."""
import streamlit as st

st.set_page_config(page_title="Diretor.IA — EnerMais", page_icon="📊", layout="wide")

import acesso                      # noqa: E402
import auth                        # noqa: E402
import base                        # noqa: E402
import estilo                      # noqa: E402
import logs_app                    # noqa: E402
from conexao import get_banco      # noqa: E402

estilo.aplicar()
usuario = auth.require_login(registrar_falha=lambda: logs_app.registrar(get_banco(), "aviso", "login", "falha_login", "Tentativa de login inválida"))
papel = base.resolver_papel(usuario)           # st.stop() aqui se nao tem acesso ativo

st.sidebar.caption(f"Logado como `{usuario}`")
if st.sidebar.button("Sair"):
    logs_app.registrar(get_banco(), "evento", "acesso", "logout", "Saída do painel", usuario=usuario)
    auth.sair()
    st.rerun()

paginas = [
    st.Page("telas/1_Visao_geral.py", title="Visão geral", icon="🏠", default=True, url_path="visao-geral"),
    st.Page("telas/2_Categorias.py", title="Categorias", icon="🗂️", url_path="categorias"),
    st.Page("telas/3_Entregaveis.py", title="Entregáveis", icon="📋", url_path="entregaveis"),
    st.Page("telas/4_Reports_recebidos.py", title="Reports recebidos", icon="📨", url_path="reports"),
    st.Page("telas/5_Prontidao_fontes.py", title="Prontidão e fontes", icon="🔌", url_path="prontidao"),
    st.Page("telas/6_Ajuda.py", title="Ajuda", icon="❓", url_path="ajuda"),
]
if papel == acesso.ADMIN:                      # Logs: so o administrador (a pagina nem e registrada para o Diretor)
    paginas.append(st.Page("telas/7_Logs.py", title="Logs (admin)", icon="🧾", url_path="logs"))
base.rodape()
st.navigation(paginas).run()
