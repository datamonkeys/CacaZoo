"""Injeta anãs marrons sintéticas em objetos reais do Backyard Worlds e mede
quantas o detector põe acima do 95º percentil dos objetos sem injeção.

    python -m caca_zoo --n 300 --projeto byw     # uma vez, para ter imagens
    python -m validacao.injecao_byw [--n 300]    # ~7 min para 300 objetos
"""

from __future__ import annotations

import argparse
import os
import tempfile

import numpy as np
from PIL import Image

from caca_zoo.detectores import nota_byw
from validacao._dados import imagens, resultados

AMPLITUDES = (60, 120, 200)


def injetar(imgs: list[str], pasta: str, rng: np.random.Generator, amp: float) -> tuple[list[str], tuple[float, float]]:
    """Grava cópias com um objeto escuro andando em linha reta; devolve as cópias e o ponto final."""
    h, w = np.asarray(Image.open(imgs[0])).shape[:2]
    x0, y0 = rng.uniform(150, w - 150), rng.uniform(150, h - 150)
    passo, ang = rng.uniform(30, 120), rng.uniform(0, 2 * np.pi)
    yy, xx = np.mgrid[:h, :w]
    novos = []
    for k, p in enumerate(imgs):
        f = k / (len(imgs) - 1)
        cx, cy = x0 + np.cos(ang) * passo * f, y0 + np.sin(ang) * passo * f
        psf = amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 14**2))
        im = np.asarray(Image.open(p).convert("RGB"), np.float32) - psf[..., None]
        q = os.path.join(pasta, f"{k}.png")
        Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(q)
        novos.append(q)
    return novos, (x0 + np.cos(ang) * passo, y0 + np.sin(ang) * passo)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=300, help="objetos da amostra (fixa, para ser reproduzível)")
    n = ap.parse_args().n
    rng = np.random.default_rng(1)
    limpos, achados = [], []
    with tempfile.TemporaryDirectory() as pasta:
        for it in resultados("byw")[:n]:
            imgs = imagens(it)
            limpos.append(nota_byw(imgs)[0])
            for amp in AMPLITUDES:
                novos, (ex, ey) = injetar(imgs, pasta, rng, amp)
                nota, _, extra = nota_byw(novos)
                px, py = extra["pos"]
                achados.append((amp, nota, bool(np.hypot(px - ex, py - ey) < 30)))
    corte = float(np.percentile(limpos, 95))
    print(f"sem injeção: mediana {np.median(limpos):.1f}, p95 {corte:.1f}, max {max(limpos):.1f}")
    for amp in AMPLITUDES:
        sel = [a for a in achados if a[0] == amp]
        recuperadas = np.mean([nota > corte and ok for _, nota, ok in sel])
        print(f"amp {amp}: recuperadas {recuperadas:.0%} (nota mediana {np.median([s[1] for s in sel]):.1f})")


if __name__ == "__main__":
    main()
