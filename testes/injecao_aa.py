"""Injeta caudas sintéticas no objeto central de objetos reais do Active Asteroids
e compara a nota com a dos mesmos objetos sem cauda."""
import json, os, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

rng = np.random.default_rng(2)
from _dados import resultados
dados = resultados("aa")
arq = lambda u: os.path.join(caca.CACHE, u.rsplit("/", 1)[-1])
tmp = tempfile.mkdtemp()
limpos, achados = [], []
for it in dados:
    imgs = [arq(u) for u in it["urls"]]
    limpos.append(caca.nota_aa(imgs)[0])
    for amp in (25, 50, 100):
        ang = rng.uniform(0, 2 * np.pi)
        novos = []
        for k, p in enumerate(imgs):
            im = np.asarray(Image.open(p).convert("RGB"), np.float32)
            h, w = im.shape[:2]
            yy, xx = np.mgrid[:h, :w] - np.array([h // 2, w // 2])[:, None, None]
            ao_longo = xx * np.cos(ang) + yy * np.sin(ang)
            de_lado = -xx * np.sin(ang) + yy * np.cos(ang)
            # cauda: cai com a distância, abre em leque, só de um lado
            cauda = amp * np.exp(-ao_longo / 15) * np.exp(-de_lado ** 2 / (2 * (2 + 0.3 * ao_longo) ** 2))
            cauda[ao_longo < 2] = 0
            im = im - cauda[..., None]  # estrelas escuras neste projeto
            q = os.path.join(tmp, f"{k}.png")
            Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(q)
            novos.append(q)
        achados.append((amp, caca.nota_aa(novos)[0]))

limpos = np.array(limpos)
lim = np.percentile(limpos, 95)
print(f"sem cauda: mediana {np.median(limpos):.1f}, p95 {lim:.1f}, max {limpos.max():.1f}, sem alvo {np.mean(limpos == 0):.0%}")
for amp in (25, 50, 100):
    ns = np.array([n for a, n in achados if a == amp])
    print(f"cauda {amp}: acima do p95 {np.mean(ns > lim):.0%} (nota mediana {np.median(ns):.1f})")
