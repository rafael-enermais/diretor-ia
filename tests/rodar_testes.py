# -*- coding: utf-8 -*-
"""Roda todos os testes sem precisar do pytest:  python tests/rodar_testes.py   (sai com codigo 1 se algum falhar)."""
import importlib
import pathlib
import sys
import traceback

RAIZ = pathlib.Path(__file__).resolve().parent.parent
for p in (RAIZ / "app", RAIZ / "tests"):
    sys.path.insert(0, str(p))


def main() -> int:
    ok = falhas = 0
    for arq in sorted((RAIZ / "tests").glob("test_*.py")):
        mod = importlib.import_module(arq.stem)
        for nome in sorted(n for n in dir(mod) if n.startswith("test_")):
            try:
                getattr(mod, nome)()
                ok += 1
            except Exception:                                   # noqa: BLE001
                falhas += 1
                print(f"FALHOU  {arq.stem}.{nome}")
                traceback.print_exc()
    print(f"\n{ok} testes passaram, {falhas} falharam.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
