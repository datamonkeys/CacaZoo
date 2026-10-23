"""Dados de entrada das validações com imagens reais."""

from __future__ import annotations

import os
import sys
from typing import Any

from caca_zoo import rede, zooniverse

# conjunto "gen3_feedback_training" do Kilonova Seekers: 51 objetos rotulados pela equipe
SET_TREINO_KN = 134144


def resultados(projeto: str, minimo: int = 10) -> list[dict[str, Any]]:
    """Objetos de uma rodada anterior (as validações usam imagens reais em cache)."""
    itens = rede.ler_json(os.path.join(rede.PASTA, "resultados.json"), {}).get(projeto, [])
    if len(itens) < minimo:
        sys.exit(f"precisa de uma rodada antes: python -m caca_zoo --n 300 --projeto {projeto}")
    return itens


def treino_kn() -> list[dict[str, Any]]:
    """Objetos de treino rotulados do Kilonova Seekers; baixa na primeira vez."""
    caminho = os.path.join(rede.CACHE, "kn_treino.json")
    subs = rede.ler_json(caminho, None)
    if subs is None:
        os.makedirs(rede.CACHE, exist_ok=True)
        subs = rede.get_json(f"{zooniverse.API}/subjects?subject_set_id={SET_TREINO_KN}&page_size=100")["subjects"]
        rede.gravar_json(caminho, subs)
    return subs


def imagens(item: dict[str, Any]) -> list[str]:
    """Caminhos locais das imagens de um objeto já baixado."""
    return [os.path.join(rede.CACHE, u.rsplit("/", 1)[-1]) for u in item["urls"]]


def auc(positivos: list[float], negativos: list[float]) -> float:
    """Probabilidade de um positivo ter nota maior que um negativo (0.5 = chute)."""
    pares = [(a > b) + 0.5 * (a == b) for a in positivos for b in negativos]
    return sum(pares) / len(pares) if pares else float("nan")
