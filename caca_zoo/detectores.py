"""Os três detectores. Cada um devolve (nota, motivo[, extra])."""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

from .imagem import cinza, ruido


def nota_byw(imgs: list[str]) -> tuple[float, str, dict[str, Any]]:
    """Mover: no fundo branco as estrelas são escuras. Um objeto que se move
    deixa um par 'some aqui / aparece ali' entre o primeiro e o último quadro,
    enquanto estrelas paradas se cancelam."""
    quadros = np.array([255 - cinza(p) for p in imgs])
    # ~14 épocas ao longo de anos: mediana do início contra a do fim maximiza
    # o deslocamento e apaga a oscilação de cor das estrelas paradas
    t = max(1, len(quadros) // 3)
    a = ndimage.gaussian_filter(np.median(quadros[:t], 0), 2)
    b = ndimage.gaussian_filter(np.median(quadros[-t:], 0), 2)
    d = b - a
    s = ruido(d)
    pos, neg = d / s, -d / s
    # descarta a borda e a grade vermelha
    m = 20
    pos[:m], pos[-m:], pos[:, :m], pos[:, -m:] = 0, 0, 0, 0
    neg[:m], neg[-m:], neg[:, :m], neg[:, -m:] = 0, 0, 0, 0
    # estrela parada aparece em todas as épocas; quem se move, não
    # (relativo ao fundo: no plano da galáxia o fundo inteiro é escuro)
    piso = ndimage.gaussian_filter(np.percentile(quadros, 20, axis=0), 2)
    fixo = piso - np.median(piso) > 60
    # miolo saturado muda de cor e abre buraco na máscara; fecha
    # estrela saturada: anel preto com miolo que "estoura" em branco em
    # algumas épocas; preenche o miolo (a grade vermelha não chega a 235)
    saturada = ndimage.binary_fill_holes(ndimage.binary_closing(quadros.max(0) > 235, iterations=3))
    # só a saturação de estrela parada; mover brilhante também satura, mas anda
    rot, _ = ndimage.label(saturada)
    parada = np.isin(rot, np.unique(rot[fixo & saturada]))
    parada[rot == 0] = False
    sat = ndimage.binary_dilation(fixo, iterations=10) | ndimage.binary_dilation(parada, iterations=30)
    pos[sat], neg[sat] = 0, 0
    yp, xp = (int(v) for v in np.unravel_index(np.argmax(pos), pos.shape))
    # o par negativo tem que estar perto (anã marrom anda poucos pixels)
    r = 150  # em ~10 anos uma anã marrom próxima anda >100px nesta escala
    janela = neg[max(0, yp - r) : yp + r, max(0, xp - r) : xp + r]
    yn, xn = (int(v) for v in np.unravel_index(np.argmax(janela), janela.shape))
    dist = np.hypot(yn + max(0, yp - r) - yp, xn + max(0, xp - r) - xp)
    forca = min(pos[yp, xp], janela[yn, xn])
    nota = float(forca) if dist > 4 else float(forca) * 0.3
    xo, yo = xn + max(0, xp - r), yn + max(0, yp - r)  # onde o objeto estava no começo
    extra = {"pos": [xp, yp], "lado": [int(d.shape[1]), int(d.shape[0])], "cor": cor_byw(imgs, t, (xp, yp), (xo, yo))}
    motivo = f"par claro/escuro de {forca:.1f}σ, deslocamento {dist:.0f}px em ({xp},{yp})"
    cor = extra["cor"]
    if isinstance(cor, float):
        motivo += f", cor {cor:+.2f} ({'avermelhado, W2' if cor > 0 else 'azulado, W1'})"
        # informativa: nos movers catalogados seguiu o W1−W2 do CatWISE (r = 0.87), mas o
        # ruído também sai avermelhado (fundo do W2), então não entra na nota
    return nota, motivo, extra


def cor_byw(imgs: list[str], t: int, fim: tuple[int, int], inicio: tuple[int, int], r: int = 6) -> float | None:
    """Cor do objeto nas imagens do Backyard Worlds, onde W1 é azul e W2 laranja: quanto
    ele escurece o canal azul contra o vermelho (no fim do trajeto nas últimas épocas e
    no começo nas primeiras). > 0 = mais brilhante em W2, como uma anã marrom."""
    rgb = np.array([np.asarray(Image.open(p).convert("RGB"), np.float32) for p in imgs])
    medidas = []
    for pilha, (x, y) in ((rgb[-t:], fim), (rgb[:t], inicio)):
        img = 255 - np.median(pilha, 0)  # escurecimento por canal
        fundo = np.median(img.reshape(-1, 3), 0)
        janela = img[max(0, y - r) : y + r + 1, max(0, x - r) : x + r + 1].reshape(-1, 3) - fundo
        vermelho, azul = float(janela[:, 0].clip(0).sum()), float(janela[:, 2].clip(0).sum())
        if vermelho + azul > 50:
            medidas.append((azul - vermelho) / (azul + vermelho))
    return round(float(np.mean(medidas)), 3) if medidas else None


def nota_aa(imgs: list[str]) -> tuple[float, str]:
    """Cauda: isola a mancha ligada ao objeto central e mede quanto o centro
    de luz dela se afasta do pico. Estrela ou rastro de movimento são
    simétricos; uma cauda ou coma puxa a luz para um lado. Parâmetros
    escolhidos por injeção de caudas sintéticas (validacao/injecao_aa.py)."""
    notas, motivos = [], []
    for i, p in enumerate(imgs):
        im = 255 - cinza(p)  # neste projeto as estrelas são escuras
        im = ndimage.gaussian_filter(im - np.median(im), 2)
        s = ruido(im)
        h, w = im.shape
        cy, cx = h // 2, w // 2
        rot, _ = ndimage.label(im > 1.5 * s)
        c = rot[cy - 6 : cy + 7, cx - 6 : cx + 7]
        ids = c[c > 0]
        if not ids.size:
            notas.append(0.0)  # alvo não aparece neste quadro
            continue
        alvo = rot == int(np.argmax(np.bincount(ids)))
        area = alvo.sum()
        if area < 6 or area > 3000:
            notas.append(0.0)
            continue
        yy, xx = np.nonzero(alvo)
        pesos = im[yy, xx]
        k = np.argmax(pesos)
        desvio = np.hypot((pesos * yy).sum() / pesos.sum() - yy[k], (pesos * xx).sum() / pesos.sum() - xx[k])
        # outro pico forte dentro da mancha = estrela grudada, não cauda
        picos = (im == ndimage.maximum_filter(im, 7)) & alvo & (im > 0.4 * pesos.max())
        grudada = picos.sum() > 1
        notas.append(float(desvio) * (0.2 if grudada else 1.0))
        motivos.append(f"q{i + 1} {desvio:.1f}px" + (" (estrela grudada)" if grudada else ""))
    if not motivos:
        return 0.0, "alvo não detectado"
    # mediana: cauda real aparece em todos os quadros, estrela grudada não
    return float(np.median(notas)), "luz deslocada do pico: " + ", ".join(motivos)


def nota_kn(imgs: list[str], meta: dict[str, Any]) -> tuple[float, str]:
    """Real ou bogus. Medido contra os 51 objetos de treino rotulados pela
    equipe (validacao/treino_kn.py): o melhor sinal é a fonte aparecer no painel
    de ciência E no de diferença. Só o painel de diferença dava AUC 0.71;
    os dois juntos dão 0.84."""
    im = Image.open(imgs[0]).convert("L")
    W, H = im.size
    sx, sy = W / 900, H / 432  # o layout do triptico é fixo

    def pico(x0, x1):
        a = np.asarray(im.crop((int(x0 * sx), int(45 * sy), int(x1 * sx), int(333 * sy))), np.float32)
        h, w = a.shape
        c = ndimage.gaussian_filter(a, 1.5)[h // 2 - 12 : h // 2 + 13, w // 2 - 12 : w // 2 + 13]
        return max(0.0, float(c.max() - np.median(a)) / ruido(a))

    sci, dif = pico(8, 297), pico(604, 893)
    nota = float(np.log1p(sci) + np.log1p(dif))
    return nota, f"ciência {sci:.1f}σ, diferença {dif:.1f}σ, s2n {meta.get('s2n', '?')}, mag {meta.get('mag', '?')}"
