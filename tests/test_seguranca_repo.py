# -*- coding: utf-8 -*-
"""Varredura de seguranca do repositorio PUBLICO. Roda ANTES de todo push (python tests/rodar_testes.py).
- Nomes de pessoas: comparados por SHA-256 (os nomes em si nao ficam no codigo). Qualquer palavra do repositorio cujo hash bata falha o teste.
- Segredos: endereco de banco com senha, chaves sk-/ghp_/JWT, e-mails.
- Banco: o codigo do app nao pode ter DROP/TRUNCATE/DELETE FROM/ALTER/CREATE TABLE (so SELECT, INSERT e UPDATE em tabelas do app)."""
import hashlib
import pathlib
import re
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PULAR_PASTAS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
PULAR_ARQUIVOS = {"CLAUDE.md", "secrets.toml"}                    # ficam so no computador (estao no .gitignore)
EXT_TEXTO = {".py", ".md", ".txt", ".toml", ".example", ".json", ".yml", ".yaml", ".sql", ".cfg", ".ini", ".gitignore", ""}

HASHES_PROIBIDOS = {
    "8ee48fe8654a29e94a8fe3193acd5637b28198704af54b18f71833052ab51bba", "e5d503d4582229c4c9abe250e49654765c885eb49bb49df7f1861bb79fc7346e",
    "94aec9fbed989ece189a7e172c9cf41669050495152bc4c1dbf2a38d7fd85627", "fa39b5ce3534857ca581e69778288259531c5fd2f7c6640778f0d5a92a326ee0",
    "2c9a1c95814f31bb8459a7f7fc3536e73354699bace060e0876966878e1d1548", "f83c31f2a4558a2223e1f58d52cd7b3c8e6cf42da50dfc455f61b02b454f7bb0",
    "2bd2d3a31934d76198acc030caca4c31965474fe5fa48f35fef79d0fd74ee1b2", "79063e8037fff16d297a1fe65136f1251126cddb2cc9870ecf8d653835538e85",
    "e0cf377ea9d3feb4879a8674d5ebe0152e508d725c80248e316f0b768010b757", "7a36599e1f863ad0e5f77c1b4475746a6a56d51503ba7a97c0bc30f2176eade7",
    "5c577a0914c58b4a25d1bb5efd528b4d61253fe1b0dca29333c6c2872dedf2df",
}

PADROES_SEGREDO = [
    (re.compile(r"postgres(ql)?://[^\s:@/]+:[^\s@]+@", re.I), "endereço de banco com senha"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"), "chave sk-"),
    (re.compile(r"\b(ghp_|github_pat_)[A-Za-z0-9_]{20,}"), "token do GitHub"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}"), "token JWT"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+\.[A-Za-z]{2,}"), "e-mail"),
    (re.compile(r"\b[a-z]{20}\.supabase\.co\b"), "endereço do projeto Supabase"),
]
# Exemplos ficticios (placeholders e dados de teste) que NAO sao segredo; qualquer outro achado falha.
PERMITIDOS = {"postgresql://USUARIO:SENHA@", "postgresql://u:senha123@"}
DOMINIOS_FICTICIOS = {"b.com", "x.com", "y.com", "dominio.com", "exemplo.com"}
SQL_PROIBIDO = re.compile(r"\b(DROP\s+(TABLE|SCHEMA|ROLE|VIEW|FUNCTION)|TRUNCATE|DELETE\s+FROM|ALTER\s+(TABLE|ROLE|SCHEMA|VIEW)|CREATE\s+(TABLE|ROLE|SCHEMA))\b", re.I)


def _arquivos():
    for p in sorted(RAIZ.rglob("*")):
        if p.is_file() and not (set(p.relative_to(RAIZ).parts) & PULAR_PASTAS) and p.name not in PULAR_ARQUIVOS and p.suffix.lower() in EXT_TEXTO:
            yield p


def _palavras(texto: str):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    return set(re.findall(r"[a-z0-9]{3,}", sem_acento))


def test_sem_nomes_de_pessoas():
    achados = []
    for p in _arquivos():
        for w in _palavras(p.read_text(encoding="utf-8", errors="ignore")):
            if hashlib.sha256(w.encode()).hexdigest() in HASHES_PROIBIDOS:
                achados.append(f"{p.relative_to(RAIZ)} (uma palavra do arquivo é nome de pessoa; hash {hashlib.sha256(w.encode()).hexdigest()[:8]})")
    assert not achados, "Nome de pessoa no repositório público:\n" + "\n".join(achados)


def test_sem_segredos_nem_emails():
    achados = []
    for p in _arquivos():
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for padrao, rotulo in PADROES_SEGREDO:
            for m in padrao.finditer(txt):
                achado = m.group(0)
                if achado in PERMITIDOS or (rotulo == "e-mail" and achado.rsplit("@", 1)[-1].lower() in DOMINIOS_FICTICIOS):
                    continue
                achados.append(f"{p.relative_to(RAIZ)}: {rotulo}")
                break
    assert not achados, "Possível segredo/dado pessoal no repositório público:\n" + "\n".join(achados)


def test_gitignore_protege_segredos():
    gi = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    for item in ("secrets.toml", ".env", "CLAUDE.md", "*.xlsx", "*.csv", "*.pdf"):
        assert item in gi, f".gitignore sem {item}"


def test_codigo_do_app_so_le_e_insere():
    achados = []
    for p in sorted((RAIZ / "app").rglob("*.py")):
        for m in SQL_PROIBIDO.finditer(p.read_text(encoding="utf-8")):
            achados.append(f"{p.relative_to(RAIZ)}: {m.group(0)}")
    assert not achados, "Comando de banco proibido no app:\n" + "\n".join(achados)


def test_requirements_fixados():
    for linha in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            assert "==" in linha, f"requirement sem versão fixa: {linha}"


def test_arquivos_secretos_nao_estao_no_repositorio():
    for p in RAIZ.rglob("*"):
        if p.is_file() and not (set(p.relative_to(RAIZ).parts) & PULAR_PASTAS):
            assert p.suffix.lower() not in {".pem", ".key", ".xlsx", ".xlsm", ".csv", ".pdf", ".zip", ".exe"}, f"arquivo proibido: {p.relative_to(RAIZ)}"
