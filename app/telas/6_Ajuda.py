# -*- coding: utf-8 -*-
"""Diretor.IA - Ajuda em linguagem simples. O conteudo das telas, termos e perguntas vem de guia_app.py (a mesma fonte do Assistente). O administrador ve tambem o bloco tecnico."""
import streamlit as st

import acesso
import base
import guia_app as G

banco, usuario, papel = base.contexto()
admin = papel == acesso.ADMIN
st.title("Ajuda")

st.markdown(
    """
**Para que serve este painel.** Ele reúne, num lugar só, os **indicadores** e os **entregáveis** da matriz de metas da Diretoria Financeira, organizados por categoria, e guarda os
**reports e pendências** que chegam dos colaboradores. O painel **só lê** o que os outros apps já calcularam (por exemplo, o GDF): o número que aparece aqui é o mesmo do app de origem.
É uma ajuda à gestão, não uma trava: nada é obrigatório e nada é apagado.

**Dúvida na hora?** Pergunte ao **Assistente (IA)**, por exemplo: «como exporto as pendências?» ou «o que significa o aviso 👀?». Ele conhece este guia.
"""
)

st.subheader("Como usar cada tela")
for p in G.paginas(admin):
    with st.expander(f'{p["titulo"]}' + ("  ·  só administrador" if p.get("so_admin") else "")):
        st.markdown(f'**Para que serve.** {p["serve"]}')
        if p["como"]:
            st.markdown("**Como usar**\n\n" + "\n".join(f"{n}. {t}" for n, t in enumerate(p["como"], 1)))
        if p["dicas"]:
            st.markdown("**Bom saber**\n\n" + "\n".join(f"- {t}" for t in p["dicas"]))

st.subheader("O que significa")
for termo, expl in G.GLOSSARIO:
    st.markdown(f"- **{termo}** — {expl}")

st.subheader("Perguntas rápidas")
for pergunta, resposta in G.PERGUNTAS:
    with st.expander(pergunta):
        st.markdown(resposta)

st.markdown(
    """
**Quando o número chega.** Cada app de origem grava o resultado do mês; o painel relê o banco a cada 1 minuto (ou na hora, no botão **Atualizar agora**).
Responsáveis e colaboradores aparecem só pelo primeiro nome no Assistente.

**Segurança.** O acesso é por e-mail e senha e só entra quem estiver liberado na lista de acesso do painel. Se o seu e-mail não está na lista, o painel recusa mesmo com senha certa.
"""
)

if admin:
    st.subheader("Para o administrador")
    st.markdown(
        """
- **Código de erro.** Quando algo falha, a tela mostra um código `E-DIRETOR-AAMMDD-xxxx`. Procure esse código na tela **Logs (admin)** para ver o motivo técnico.
- **Verificação técnica.** Em **Prontidão e fontes**, o botão *Rodar verificação agora* confere login do banco, catálogo (54 + 44), acesso, visões do GDF, permissões e proteção de linha.
- **Depois de cada atualização do código (push).** No Streamlit Cloud, faça *Reboot* do app e confira a **versão** no pé do menu lateral.
- **Segredos.** Ficam só em *Settings → Secrets* do Streamlit Cloud (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ANTHROPIC_API_KEY`). Nunca no GitHub.
- **Dar ou tirar acesso.** É feito no banco (tabela de acesso), por quem administra o banco. O app só lê essa tabela.
- **Reports de outros apps.** Cada app de colaborador envia pela função `diretoria.receber_report` (veja o contrato no vault, `CONTRATO-RECEBER-REPORT`). O Diretor.IA só recebe; nada volta para o app de origem.
"""
    )
