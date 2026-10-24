"""Já é conhecido? Pixel → céu e consulta ao CatWISE2020 e ao Gaia DR3 (VizieR)."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from .rede import abrir


def ceu_byw(meta: dict[str, Any], xp: float, yp: float, largura: int = 946, altura: int = 946) -> tuple[float, float]:
    """Pixel do recorte do Backyard Worlds -> RA/Dec (norte em cima, leste à esquerda).
    O FOV vem nos metadados como "118.25 x 101.75 arcseconds" (largura x altura)."""
    ra0, de0 = float(meta["RA"]), float(meta["DEC"])
    partes = str(meta.get("FOV", "118.25")).replace("x", " ").split()
    fov_x = float(partes[0])
    fov_y = float(partes[1]) if len(partes) > 1 and partes[1].replace(".", "", 1).isdigit() else fov_x
    dx = (xp - largura / 2) * fov_x / largura
    dy = (yp - altura / 2) * fov_y / altura
    return ra0 - dx / 3600 / np.cos(np.radians(de0)), de0 - dy / 3600


def catwise_movendo(ra: float, dec: float, raio: float = 40) -> list[tuple[str, float, float | None]] | None:
    """Fontes do CatWISE2020 com movimento próprio > 0.05"/ano e > 5σ perto da posição:
    (nome, pm em "/ano, cor W1−W2 ou None). Anã marrom: W1−W2 alto (T: > 1)."""
    url = (
        "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=II/365/catwise"
        f"&-c={ra:.5f}%20{dec:+.5f}&-c.rs={raio}&-out=Name,pmRA,pmDE,e_pmRA,e_pmDE,W1mproPM,W2mproPM&-out.max=50"
    )
    try:
        linhas = abrir(url, 30, tentativas=3).decode().splitlines()
    except Exception:
        return None  # sem resposta: não dá para afirmar nada
    achados = []
    for l in linhas:
        p = l.split("\t")
        if len(p) == 7 and p[0].startswith("J"):
            try:
                pm = float(np.hypot(float(p[1]), float(p[2])))
                erro = float(np.hypot(float(p[3]), float(p[4])))
            except ValueError:
                continue
            try:
                cor: float | None = round(float(p[5]) - float(p[6]), 2)
            except ValueError:
                cor = None
            if pm > 0.05 and pm > 5 * erro:  # pm do CatWISE é ruidoso em fonte fraca
                achados.append((p[0].strip(), round(pm, 2), cor))
    return sorted(achados, key=lambda x: -x[1])


def gaia_movendo(ra: float, dec: float, raio: float = 40) -> list[tuple[str, float]] | None:
    """Estrelas do Gaia DR3 com movimento próprio > 50 mas/ano perto da posição."""
    url = (
        "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/355/gaiadr3"
        f"&-c={ra:.5f}%20{dec:+.5f}&-c.rs={raio}&-out=Source,pmRA,pmDE&-out.max=50"
    )
    try:
        linhas = abrir(url, 30, tentativas=3).decode().splitlines()
    except Exception:
        return None
    achados = []
    for l in linhas:
        p = l.split("\t")
        if len(p) == 3 and p[0].strip().isdigit():
            try:
                pm = float(np.hypot(float(p[1]), float(p[2]))) / 1000
            except ValueError:
                continue
            if pm > 0.05:
                achados.append(("Gaia DR3 " + p[0].strip(), round(pm, 3)))
    return sorted(achados, key=lambda x: -x[1])


def checar_conhecidos(itens: list[dict[str, Any]], corte: float = 6.0) -> None:
    """Só para os candidatos fortes do Backyard Worlds (consulta externa)."""
    for it in itens:
        if it["nota"] < corte or "pos" not in it or "RA" not in it["meta"]:
            continue
        ra, dec = ceu_byw(it["meta"], *it["pos"], *it.get("lado", (946, 946)))
        cw, ga = catwise_movendo(ra, dec), gaia_movendo(ra, dec)
        mov = sorted([("CWISE " + n, pm) for n, pm, _ in cw or []] + (ga or []), key=lambda x: -x[1])
        it["ceu"] = (round(ra, 5), round(dec, 5))
        if cw:
            it["cor_catwise"] = max(cw, key=lambda x: x[1])[2]  # W1−W2 do mover mais rápido
        if mov:  # basta um catálogo achar algo se movendo
            it["conhecido"] = "já catalogado: " + ", ".join(f'{n} ({pm}"/ano)' for n, pm in mov[:2])
        elif cw is None or ga is None:  # sem os dois não dá para dizer que é novo
            it["conhecido"] = "catálogo não respondeu"
        else:
            it["conhecido"] = "NADA no CatWISE/Gaia se movendo aqui — possível descoberta, confira no WiseView"
        time.sleep(0.5)
