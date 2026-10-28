# -*- coding: utf-8 -*-
"""Diretor.IA - Ajuda em linguagem simples. O administrador ve tambem o bloco tecnico."""
import streamlit as st

import acesso
import base

banco, usuario, papel = base.contexto()
st.title("Ajuda")

st.markdown(
    """
**Para que serve este painel.** Ele reúne, num lugar só, os **indicadores** e os **entregáveis** da matriz de metas da Diretoria Financeira, organizados por categoria.
O painel **só lê** o que os outros apps já calcularam (por exemplo, o GDF). Ele não recalcula nada: o número que aparece aqui é o mesmo do app de origem.

**Telas**
- **Visão geral** — quantos indicadores e entregáveis existem, quantos já têm valor e como estão (no alvo, atenção, fora da meta).
- **Categorias** — escolha uma categoria para ver cada indicador, o último valor, a meta e o status. Abra o detalhe para ver como o número foi apurado e o histórico mês a mês.
- **Entregáveis** — os entregáveis, com responsável, prazo, meta e resultado quando houver.
- **Reports recebidos** — um registro simples dos reports semanais que você recebeu (quem enviou, resumo, dificuldades). O report completo fica no app de quem o escreve.
- **Prontidão e fontes** — o que já está ligado a uma fonte e recebendo dado, e o que ainda falta chegar.

**Como ler o status**
- 🟢 **No alvo** — dentro da meta.
- 🟡 **Atenção** — perto do limite da meta.
- 🔴 **Fora da meta** — fora da meta.
- ⚪ **Sem lançamento** — o dado ainda não chegou. *Não significa que esteja ruim: significa que falta o número.*
- Quando um indicador tem mais de uma linha (por empresa ou obra), o status do indicador é o **pior** entre elas, e o detalhe mostra cada linha.

**Quando o número chega.** Cada app de origem grava o resultado do mês; o painel relê o banco a cada 1 minuto (ou na hora, no botão **Atualizar agora**).
Responsáveis aparecem só pelo primeiro nome.

**Segurança.** O acesso é por e-mail e senha e só entra quem estiver liberado na lista de acesso do painel. Se o seu e-mail não está na lista, o painel recusa mesmo com senha certa.
"""
)

if papel == acesso.ADMIN:
    st.subheader("Para o administrador")
    st.markdown(
        """
- **Código de erro.** Quando algo falha, a tela mostra um código `E-DIRETOR-AAMMDD-xxxx`. Procure esse código na tela **Logs (admin)** para ver o motivo técnico.
- **Verificação técnica.** Em **Prontidão e fontes**, o botão *Rodar verificação agora* confere login do banco, catálogo (54 + 44), acesso, visões do GDF, permissões e proteção de linha.
- **Depois de cada atualização do código (push).** No Streamlit Cloud, faça *Reboot* do app e confira a **versão** no pé do menu lateral.
- **Segredos.** Ficam só em *Settings → Secrets* do Streamlit Cloud (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`). Nunca no GitHub.
- **Dar ou tirar acesso.** É feito no banco (tabela de acesso), por quem administra o banco. O app só lê essa tabela.
"""
    )
