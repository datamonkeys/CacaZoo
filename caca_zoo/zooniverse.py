"""Projetos, fila de objetos na API Panoptes e avaliação de cada objeto."""

from __future__ import annotations

import time
from typing import Any

from .detectores import nota_aa, nota_byw, nota_kn
from .rede import baixar, get_json
from .registro import obter

API = "https://www.zooniverse.org/api"


PROJETOS: dict[str, dict[str, Any]] = {
    "byw": dict(
        nome="Backyard Worlds: Cool Neighbors",
        slug="coolneighbors/backyard-worlds-cool-neighbors",
        workflow=24299,
        alvo="anãs marrons que se movem",
    ),
    "aa": dict(nome="Active Asteroids", slug="orionnau/active-asteroids", workflow=32745, alvo="asteroides com cauda/coma"),
    "kn": dict(
        nome="Kilonova Seekers",
        slug="tkillestein/kilonova-seekers",
        workflow=30925,
        alvo="transientes reais (supernovas, kilonovas)",
    ),
}


def fila(workflow: int, n: int) -> list[dict[str, Any]]:
    """Objetos na fila do workflow, sem repetir."""
    vistos, out = set(), []
    for _ in range(max(3, n // 5)):
        dados = get_json(f"{API}/subjects/queued?workflow_id={workflow}&page_size=10")
        for s in dados.get("subjects", []):
            if s.get("metadata", {}).get("#training_subject") is True:
                continue  # treino já tem resposta; não é descoberta
            if s["id"] not in vistos:
                vistos.add(s["id"])
                out.append(s)
        if len(out) >= n:
            break
        time.sleep(0.3)
    return out[:n]


def avaliar(chave: str, s: dict[str, Any]) -> dict[str, Any]:
    urls = [list(l.values())[0] for l in s["locations"]]
    imgs = [baixar(u) for u in urls]
    meta = s.get("metadata", {})
    extra: dict[str, Any] = {}
    if chave == "byw":
        nota, motivo, extra = nota_byw(imgs)
    elif chave == "aa":
        nota, motivo = nota_aa(imgs)
    else:
        nota, motivo = nota_kn(imgs, meta)
    return dict(id=s["id"], urls=urls, nota=round(nota, 2), motivo=motivo, meta=meta, **extra)


def _seguro(chave: str, s: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return avaliar(chave, s)
    except Exception as e:  # um objeto quebrado não derruba a rodada
        obter().warning("erro_no_objeto", projeto=chave, id=s.get("id"), erro=repr(e))
        return None
