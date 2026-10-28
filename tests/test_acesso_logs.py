# -*- coding: utf-8 -*-
import re

import acesso
import logs_app
from fakes import BancoFalso


def test_decidir_papel_fail_closed():
    assert acesso.decidir_papel(None) is None
    assert acesso.decidir_papel({}) is None
    assert acesso.decidir_papel({"papel": "admin", "ativo": False}) is None
    assert acesso.decidir_papel({"papel": "admin", "ativo": None}) is None
    assert acesso.decidir_papel({"papel": "admin", "ativo": "true"}) is None        # so True de verdade
    assert acesso.decidir_papel({"papel": "root", "ativo": True}) is None            # papel desconhecido
    assert acesso.decidir_papel({"papel": "admin", "ativo": True}) == "admin"
    assert acesso.decidir_papel({"papel": "diretor", "ativo": True}) == "diretor"


def test_papel_do_usuario():
    b = BancoFalso([[{"papel": "diretor", "ativo": True}]])
    assert acesso.papel_do_usuario(b, "  Alguem@Exemplo.com ") == "diretor"
    assert b.consultas[0][1] == ("alguem@exemplo.com",)                                # e-mail normalizado
    assert acesso.papel_do_usuario(BancoFalso([[]]), "x@y.com") is None                # nao esta na tabela
    assert acesso.papel_do_usuario(BancoFalso(), "sem-arroba") is None                 # nem consulta
    assert acesso.papel_do_usuario(BancoFalso(), "") is None


def test_erro_de_banco_nao_libera():
    try:
        acesso.papel_do_usuario(BancoFalso(falhar=True), "a@b.com")
    except RuntimeError:
        return
    raise AssertionError("erro de banco deveria subir (quem chama nega o acesso)")


def test_mascarar():
    t = logs_app.mascarar("falhou postgresql://u:senha123@host:5432/db e sk-abcdefghijk e a@b.com Bearer abc.def password=segredo")
    assert "senha123" not in t and "host:5432" not in t and "sk-abcdefghijk" not in t and "a@b.com" not in t and "segredo" not in t
    assert "eyJhbGciOiJIUzI1NiJ9.abc.def" not in logs_app.mascarar("token eyJhbGciOiJIUzI1NiJ9.abc.def")


def test_codigo_de_erro():
    assert re.fullmatch(r"E-DIRETOR-\d{6}-[0-9A-F]{4}", logs_app.novo_codigo_erro())


def test_registrar_nunca_levanta_e_mascara():
    assert logs_app.registrar(BancoFalso(falhar=True), "erro", "t", "a", "msg") is False
    assert logs_app.registrar(None, "erro", "t", "a", "msg") is False
    assert logs_app.registrar(BancoFalso(), "nivel-invalido", "t", "a", "msg") is False
    b = BancoFalso()
    assert logs_app.registrar(b, "evento", "tela", "acao", "ok", usuario="quem@dominio.com", contexto={"senha": "x", "n": 1, "txt": "a@b.com"}) is True
    sql, params = b.comandos[0]
    assert "diretoria.registrar_log" in sql
    assert params[2] == "quem@dominio.com"                                              # usuario do log fica legivel (o log e so do admin)
    assert '"senha": "***"' in params[8] and "a@b.com" not in params[8]                 # campo sensivel e e-mail no contexto saem


def test_registrar_erro_devolve_codigo():
    b = BancoFalso()
    cod = logs_app.registrar_erro(b, "tela", "acao", ValueError("boom"), usuario="u@x.com")
    assert re.fullmatch(r"E-DIRETOR-\d{6}-[0-9A-F]{4}", cod)
    assert b.comandos[0][1][5] == cod
    assert re.fullmatch(r"E-DIRETOR-\d{6}-[0-9A-F]{4}", logs_app.registrar_erro(BancoFalso(falhar=True), "t", "a", ValueError("x")))   # sem banco, ainda devolve codigo
