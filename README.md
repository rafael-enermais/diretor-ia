# Diretor.IA

Painel da Diretoria Financeira (Streamlit + Supabase). Mostra os indicadores e as entregas da matriz de metas, por categoria, lendo as
visoes ja calculadas pelos outros apps (o Diretor.IA nao recalcula nada). Acesso fechado por padrao: so entra quem esta na tabela de acesso.

- Rodar local: `pip install -r requirements.txt` e `streamlit run app/app.py` (precisa de `.streamlit/secrets.toml`, veja `.streamlit/secrets.toml.example`).
- Chat IA (somente leitura): precisa dos secrets `ANTHROPIC_API_KEY` (e opcional `ANTHROPIC_MODEL`). Memoria da conversa: tabelas do SQL-03 (sem elas, a conversa vale so na sessao).
- Testes: `python tests/rodar_testes.py` (sem banco) ou `pytest tests`.
- Este repositorio e publico: nao tem dado real, nome de pessoa, e-mail nem chave.
