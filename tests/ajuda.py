"""Imagens sintéticas para os testes (nada é baixado)."""

import os

import numpy as np
from PIL import Image


def salvar(d, nome, arr):
    p = os.path.join(d, nome)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(p)
    return p


def mancha(h, w, x, y, amp, sig):
    yy, xx = np.mgrid[:h, :w]
    return amp * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sig**2))


def quadros_byw(d, mover=True):
    """12 épocas no fundo branco: uma estrela parada e (opcional) uma anã marrom andando."""
    rng = np.random.default_rng(0)
    h = w = 400
    fixa = mancha(h, w, 100, 300, 120, 10)
    out = []
    for k in range(12):
        x = 150 + 6 * k if mover else 150
        escuro = fixa + mancha(h, w, x, 200, 120, 10) + rng.normal(0, 2, (h, w))
        out.append(salvar(d, f"q{k}.png", np.repeat((255 - escuro)[..., None], 3, 2)))
    return out


def quadros_aa(d, cauda):
    """5 quadros com o asteroide no centro, com ou sem cauda para a direita."""
    rng = np.random.default_rng(1)
    h = w = 160
    out = []
    for k in range(5):
        luz = mancha(h, w, 80, 80, 150, 3) + rng.normal(0, 3, (h, w))
        if cauda:
            for i in range(1, 25):
                luz += mancha(h, w, 80 + i, 80, 60 * np.exp(-i / 10), 2 + 0.1 * i)
        out.append(salvar(d, f"a{k}.png", np.repeat((200 - luz)[..., None], 3, 2)))
    return out
