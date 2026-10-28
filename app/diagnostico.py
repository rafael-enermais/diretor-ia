# -*- coding: utf-8 -*-
"""Diretor.IA - verificacao tecnica (so o administrador ve): confere conexao, tabelas, visoes, permissoes e gravacao de log.
So le e testa (nao altera dado). Cada verificacao e independente: uma que falha nao esconde as outras. Nunca mostra endereco de banco nem chave."""
from __future__ import annotations

from logs_app import mascarar


def _rodar(nome, funcao):
    try:
        ok, detalhe = funcao()
        return {"verificacao": nome, "ok": bool(ok), "detalhe": detalhe}
    except Exception as exc:                                    # noqa: BLE001
        return {"verificacao": nome, "ok": False, "detalhe": f"{type(exc).__name__}: {mascarar(exc, 200)}"}


def rodar(banco) -> list:
    def usuario_banco():
        u = banco.consultar("SELECT current_user AS u")[0]["u"]
        return u == "app_diretoria", f"conectado como `{u}`"

    def catalogo_cont():
        c = {r["tipo"]: r["n"] for r in banco.consultar("SELECT tipo, count(*) AS n FROM diretoria.catalogo_item WHERE ativo GROUP BY tipo")}
        return c.get("indicador") == 54 and c.get("entrega") == 44, f"{c.get('indicador', 0)} indicadores e {c.get('entrega', 0)} entregáveis (esperado 54 e 44)"

    def acesso_cont():
        n = banco.consultar("SELECT count(*) AS n FROM diretoria.acesso WHERE ativo")[0]["n"]
        return n >= 1, f"{n} usuário(s) com acesso ativo"

    def visao_atual():
        n = banco.consultar("SELECT count(*) AS n FROM diretoria.metricas_atual")[0]["n"]
        return True, f"visão `metricas_atual` legível: {n} linha(s)" + ("" if n else " (ainda sem mês gravado no GDF)")

    def visao_hist():
        n = banco.consultar("SELECT count(*) AS n FROM diretoria.metricas")[0]["n"]
        return True, f"visão `metricas` legível: {n} linha(s)"

    def sem_delete():
        r = banco.consultar("""SELECT has_table_privilege('app_diretoria','diretoria.report_recebido','DELETE') AS a,
                                      has_table_privilege('app_diretoria','diretoria.acesso','INSERT') AS b,
                                      has_table_privilege('app_diretoria','diretoria.catalogo_item','UPDATE') AS c""")[0]
        return not (r["a"] or r["b"] or r["c"]), "sem DELETE em report_recebido, sem escrita em acesso e catalogo_item (esperado)"

    def rls():
        linhas = banco.consultar("SELECT relname, relrowsecurity AS rls FROM pg_class WHERE relnamespace = 'diretoria'::regnamespace AND relkind = 'r' "
                                 "AND relname IN ('acesso','catalogo_item','report_recebido','app_log') ORDER BY 1")
        sem = [l["relname"] for l in linhas if not l["rls"]]
        return len(linhas) == 4 and not sem, f"{len(linhas)} tabelas conferidas; sem proteção de linha: {', '.join(sem) or 'nenhuma'}"

    def gdf_fechado():
        r = banco.consultar("SELECT has_table_privilege('app_diretoria','gdf.metrica_registro','SELECT') AS a")[0]
        return not r["a"], "sem acesso direto às tabelas do GDF (esperado: só as visões)"

    return [
        _rodar("Login do banco", usuario_banco), _rodar("Catálogo carregado", catalogo_cont), _rodar("Tabela de acesso", acesso_cont),
        _rodar("Visão das métricas atuais", visao_atual), _rodar("Visão do histórico", visao_hist), _rodar("Permissões mínimas", sem_delete),
        _rodar("Proteção de linha (RLS)", rls), _rodar("Tabelas do GDF fechadas", gdf_fechado),
    ]
