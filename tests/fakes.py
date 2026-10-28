# -*- coding: utf-8 -*-
"""Banco falso para testes (sem rede, sem Postgres): grava os comandos recebidos e devolve respostas combinadas."""


class BancoFalso:
    def __init__(self, respostas=None, falhar=False):
        self.respostas = respostas or []          # lista de respostas, uma por chamada a consultar()
        self.falhar = falhar
        self.consultas, self.comandos, self.transacoes = [], [], []

    def consultar(self, sql, params=None):
        if self.falhar:
            raise RuntimeError("banco fora do ar")
        self.consultas.append((sql, params))
        return self.respostas.pop(0) if self.respostas else []

    def executar(self, sql, params=None):
        if self.falhar:
            raise RuntimeError("banco fora do ar")
        self.comandos.append((sql, params))

    def executar_varios(self, comandos):
        if self.falhar:
            raise RuntimeError("banco fora do ar")
        self.transacoes.append(list(comandos))
