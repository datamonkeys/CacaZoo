"""Leitura das imagens e ruído robusto."""

from __future__ import annotations

import numpy as np
from PIL import Image


def cinza(caminho: str) -> np.ndarray:
    return np.asarray(Image.open(caminho).convert("L"), dtype=np.float32)


def ruido(a: np.ndarray) -> float:
    """Desvio robusto; fundos quase constantes (PNG quantizado) têm MAD zero,
    então usa o desvio padrão da faixa central dos valores com piso de 1 nível."""
    lo, hi = np.percentile(a, [5, 95])
    meio = a[(a >= lo) & (a <= hi)]
    return max(float(meio.std()), 1.0)
