"""Injeta anãs marrons sintéticas em objetos reais do Backyard Worlds e mede
quantas o detector põe acima do limiar, contra a nota dos objetos sem injeção."""
import json, os, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

rng = np.random.default_rng(1)
from _dados import resultados
# amostra fixa para a validação ser reproduzível e rodar em minutos: --n 300 (padrão)
N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 300
dados = resultados("byw")[:N]
arq = lambda u: os.path.join(caca.CACHE, u.rsplit("/", 1)[-1])
tmp = tempfile.mkdtemp()
limpos, achados = [], []
for it in dados:
    imgs = [arq(u) for u in it["urls"]]
    limpos.append(caca.nota_byw(imgs)[0])
    for amp in (60, 120, 200):
        h, w = np.asarray(Image.open(imgs[0])).shape[:2]
        x0, y0 = rng.uniform(150, w - 150), rng.uniform(150, h - 150)
        passo = rng.uniform(30, 120)
        ang = rng.uniform(0, 2 * np.pi)
        yy, xx = np.mgrid[:h, :w]
        novos = []
        for k, p in enumerate(imgs):
            f = k / (len(imgs) - 1)
            cx, cy = x0 + np.cos(ang) * passo * f, y0 + np.sin(ang) * passo * f
            psf = amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 14 ** 2))
            im = np.asarray(Image.open(p).convert("RGB"), np.float32) - psf[..., None]
            q = os.path.join(tmp, f"{k}.png")
            Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(q)
            novos.append(q)
        nota, motivo, extra = caca.nota_byw(novos)
        # acertou se apontou para o ponto final da injeção
        ex, ey = x0 + np.cos(ang) * passo, y0 + np.sin(ang) * passo
        px, py = extra["pos"]
        achados.append((amp, nota, np.hypot(px - ex, py - ey) < 30))
        if os.environ.get("DEBUG"): print(f"{len(imgs)}q passo {passo:.0f} amp {amp} nota {nota:.1f} {motivo}")

limpos = np.array(limpos)
lim = np.percentile(limpos, 95)
print(f"sem injeção: mediana {np.median(limpos):.1f}, p95 {lim:.1f}, max {limpos.max():.1f}")
for amp in (60, 120, 200):
    sel = [a for a in achados if a[0] == amp]
    rec = np.mean([n > lim and ok for _, n, ok in sel])
    print(f"amp {amp}: recuperadas {rec:.0%} (nota mediana {np.median([n for _, n, _ in sel]):.1f}, posição certa {np.mean([ok for *_, ok in sel]):.0%})")
