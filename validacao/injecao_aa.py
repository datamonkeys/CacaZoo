"""Injeta caudas sintéticas no objeto central de objetos reais do Active
Asteroids e compara a nota com a dos mesmos objetos sem cauda.

    python -m caca_zoo --n 100 --projeto aa      # uma vez, para ter imagens
    python -m validacao.injecao_aa
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
from PIL import Image

from caca_zoo.detectores import nota_aa
from validacao._dados import imagens, resultados

AMPLITUDES = (25, 50, 100)


def com_cauda(imgs: list[str], pasta: str, ang: float, amp: float) -> list[str]:
    """Cópias com uma cauda que cai com a distância e abre em leque, só de um lado."""
    novos = []
    for k, p in enumerate(imgs):
        im = np.asarray(Image.open(p).convert("RGB"), np.float32)
        h, w = im.shape[:2]
        yy, xx = np.mgrid[:h, :w] - np.array([h // 2, w // 2])[:, None, None]
        ao_longo = xx * np.cos(ang) + yy * np.sin(ang)
        de_lado = -xx * np.sin(ang) + yy * np.cos(ang)
        cauda = amp * np.exp(-ao_longo / 15) * np.exp(-(de_lado**2) / (2 * (2 + 0.3 * ao_longo) ** 2))
        cauda[ao_longo < 2] = 0
        q = os.path.join(pasta, f"{k}.png")
        Image.fromarray(np.clip(im - cauda[..., None], 0, 255).astype(np.uint8)).save(q)  # estrelas escuras
        novos.append(q)
    return novos


def main() -> None:
    rng = np.random.default_rng(2)
    limpos, achados = [], []
    with tempfile.TemporaryDirectory() as pasta:
        for it in resultados("aa"):
            imgs = imagens(it)
            limpos.append(nota_aa(imgs)[0])
            for amp in AMPLITUDES:
                achados.append((amp, nota_aa(com_cauda(imgs, pasta, rng.uniform(0, 2 * np.pi), amp))[0]))
    corte = float(np.percentile(limpos, 95))
    sem_alvo = np.mean(np.array(limpos) == 0)
    print(f"sem cauda: mediana {np.median(limpos):.1f}, p95 {corte:.1f}, max {max(limpos):.1f}, sem alvo {sem_alvo:.0%}")
    for amp in AMPLITUDES:
        notas = np.array([n for a, n in achados if a == amp])
        print(f"cauda {amp}: acima do p95 {np.mean(notas > corte):.0%} (nota mediana {np.median(notas):.1f})")


if __name__ == "__main__":
    main()
