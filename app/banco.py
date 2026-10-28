# -*- coding: utf-8 -*-
"""Diretor.IA - acesso ao banco (psycopg2) SEM Streamlit, para poder testar sem tela.
Uma conexao so, compartilhada pelas pessoas que usam o app ao mesmo tempo; uma trava garante que um comando nao entre no meio da transacao de outro."""
from __future__ import annotations

import threading


class Banco:
    """Envolve uma conexao psycopg2 (autocommit ligado). consultar() devolve lista de dicts; executar() nao devolve nada."""

    def __init__(self, conn):
        self.conn = conn
        self.trava = threading.RLock()

    def consultar(self, sql: str, params=None) -> list:
        with self.trava:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return []
                colunas = [d[0] for d in cur.description]
                return [dict(zip(colunas, linha)) for linha in cur.fetchall()]

    def executar(self, sql: str, params=None) -> None:
        with self.trava:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)

    def executar_varios(self, comandos) -> None:
        """Roda varios comandos [(sql, params), ...] numa transacao so: ou todos valem, ou nenhum (ROLLBACK se um falhar)."""
        with self.trava:
            self.conn.autocommit = False
            try:
                with self.conn.cursor() as cur:
                    for sql, params in comandos:
                        cur.execute(sql, params)
                self.conn.commit()
            except Exception:
                try:
                    self.conn.rollback()
                except Exception:                               # noqa: BLE001
                    pass
                raise
            finally:
                try:
                    self.conn.autocommit = True
                except Exception:                               # noqa: BLE001
                    pass

    def viva(self) -> bool:
        """True se a conexao ainda responde (o pooler derruba conexoes ociosas)."""
        if self.conn is None or getattr(self.conn, "closed", 1):
            return False
        try:
            self.consultar("SELECT 1")
            return True
        except Exception:                                       # noqa: BLE001
            return False
