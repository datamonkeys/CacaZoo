"""Mede o detector do Kilonova Seekers contra os 51 objetos de treino que a
equipe rotulou (real x bogus). Imprime a AUC: 0.5 = chute, 1.0 = perfeito."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

from _dados import treino_kn
subs = treino_kn()
reais, bogus = [], []
for s in subs:
    r = caca.avaliar("kn", s)
    real = s["metadata"].get("#feedback_1_answer") == "0"
    (reais if real else bogus).append(r["nota"])

def auc(p, n):
    return np.mean([(a > b) + 0.5 * (a == b) for a in p for b in n])

print(f"{len(reais)} reais, {len(bogus)} bogus — AUC {auc(reais, bogus):.2f}")
s2n = lambda x: float(x["metadata"].get("s2n") or 0)
print(f"só o s2n do projeto: AUC {auc([s2n(s) for s in subs if s['metadata'].get('#feedback_1_answer') == '0'], [s2n(s) for s in subs if s['metadata'].get('#feedback_1_answer') != '0']):.2f}")
