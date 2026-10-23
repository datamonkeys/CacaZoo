"""Procura os parâmetros do detector de cauda que melhor separam caudas
sintéticas de objetos limpos."""
import itertools, json, os, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

def nota(ims, suav, lim, norm, pen, agg='max'):
    notas = []
    for im in ims:
        im = ndimage.gaussian_filter(im - np.median(im), suav)
        s = caca.ruido(im)
        h, w = im.shape
        cy, cx = h // 2, w // 2
        rot, _ = ndimage.label(im > lim * s)
        c = rot[cy - 6:cy + 7, cx - 6:cx + 7]
        ids = c[c > 0]
        if not ids.size:
            notas.append(0.0); continue
        alvo = rot == np.bincount(ids).argmax()
        area = alvo.sum()
        if area < 6 or area > 3000:
            notas.append(0.0); continue
        yy, xx = np.nonzero(alvo)
        p = im[yy, xx]
        k = np.argmax(p)
        d = np.hypot((p * yy).sum() / p.sum() - yy[k], (p * xx).sum() / p.sum() - xx[k])
        n = d / np.sqrt(area / np.pi) * 10 if norm else d
        if pen:
            # outro pico forte dentro da mancha = estrela grudada
            pico = (im == ndimage.maximum_filter(im, 7)) & alvo & (im > 0.4 * p.max())
            if pico.sum() > 1:
                n *= 0.2
        notas.append(n)
    if not notas: return 0.0
    return float(np.max(notas) if agg == 'max' else np.median(notas) if agg == 'med' else np.sort(notas)[-2])

rng = np.random.default_rng(2)
dados = json.load(open(os.path.join(caca.AQUI, "resultados.json")))["aa"]
arq = lambda u: os.path.join(caca.CACHE, u.rsplit("/", 1)[-1])
limpos, caudas = [], []
for it in dados:
    base = [255 - caca.cinza(arq(u)) for u in it["urls"]]
    limpos.append(base)
    ang = rng.uniform(0, 2 * np.pi)
    com = []
    for im in base:
        h, w = im.shape
        yy, xx = np.mgrid[:h, :w] - np.array([h // 2, w // 2])[:, None, None]
        al = xx * np.cos(ang) + yy * np.sin(ang)
        la = -xx * np.sin(ang) + yy * np.cos(ang)
        t = 50 * np.exp(-al / 15) * np.exp(-la ** 2 / (2 * (2 + 0.3 * al) ** 2))
        t[al < 2] = 0
        com.append(np.clip(im + t, 0, 255))
    caudas.append(com)

for suav, lim, agg in itertools.product((1, 2, 3), (1.5, 2.5), ("max", "med", "2o")):
    L = np.array([nota(x, suav, lim, 0, 1, agg) for x in limpos])
    C = np.array([nota(x, suav, lim, 0, 1, agg) for x in caudas])
    corte = np.percentile(L, 95)
    print(f"suav {suav} lim {lim} {agg}: recupera {np.mean(C > corte):.0%}")
