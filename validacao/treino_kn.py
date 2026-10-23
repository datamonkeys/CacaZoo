"""Mede o detector do Kilonova Seekers contra os 51 objetos de treino que a
equipe rotulou (real x bogus).

    python -m validacao.treino_kn     # baixa o conjunto na primeira vez
"""

from __future__ import annotations

from caca_zoo.zooniverse import avaliar
from validacao._dados import auc, treino_kn


def main() -> None:
    reais, bogus, s2n_reais, s2n_bogus = [], [], [], []
    for s in treino_kn():
        nota = avaliar("kn", s)["nota"]
        s2n = float(s["metadata"].get("s2n") or 0)
        if s["metadata"].get("#feedback_1_answer") == "0":
            reais.append(nota)
            s2n_reais.append(s2n)
        else:
            bogus.append(nota)
            s2n_bogus.append(s2n)
    print(f"{len(reais)} reais, {len(bogus)} bogus — AUC {auc(reais, bogus):.2f}")
    print(f"só o s2n do projeto: AUC {auc(s2n_reais, s2n_bogus):.2f}")


if __name__ == "__main__":
    main()
