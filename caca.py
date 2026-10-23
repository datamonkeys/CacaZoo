#!/usr/bin/env python3
"""CacaZoo: triagem automática de objetos do Zooniverse.

Baixa os objetos na fila de três projetos onde dá para ganhar crédito de
descoberta, dá uma nota a cada um por análise de imagem e gera report.html
com os candidatos ordenados e o link para classificar no site.
A classificação continua sendo feita por você no Zooniverse.

uso: python3 caca.py [--n 40] [--projeto byw|aa|kn]
"""
import argparse, html, json, os, sys, tempfile, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
from scipy import ndimage

API = "https://www.zooniverse.org/api"
REPO = "https://github.com/louisperner/CacaZoo"
HDR = {"Accept": "application/vnd.api+json; version=1", "User-Agent": f"CacaZoo/0.2 (+{REPO})"}
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache")

PROJETOS = {
    "byw": dict(nome="Backyard Worlds: Cool Neighbors", slug="coolneighbors/backyard-worlds-cool-neighbors",
                workflow=24299, alvo="anãs marrons que se movem"),
    "aa": dict(nome="Active Asteroids", slug="orionnau/active-asteroids",
               workflow=32745, alvo="asteroides com cauda/coma"),
    "kn": dict(nome="Kilonova Seekers", slug="tkillestein/kilonova-seekers",
               workflow=30925, alvo="transientes reais (supernovas, kilonovas)"),
}


def abrir(url, timeout, tentativas=4):
    """Conteúdo da URL, com novas tentativas e espera crescente (1, 2, 4 s)."""
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(2 ** i)


def get_json(url):
    return json.loads(abrir(url, 30))


def gravar(caminho, dados):
    """Grava num temporário e troca no fim: crash ou dois threads no mesmo
    arquivo nunca deixam um arquivo pela metade no lugar."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(caminho), suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(dados)
    os.replace(tmp, caminho)


def gravar_json(caminho, obj, **kw):
    gravar(caminho, json.dumps(obj, **kw).encode())


def ler_json(caminho, padrao):
    try:
        with open(caminho) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def baixar(url):
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, url.rsplit("/", 1)[-1])
    if not os.path.exists(caminho):
        gravar(caminho, abrir(url, 60))
    return caminho


def cinza(caminho):
    return np.asarray(Image.open(caminho).convert("L"), dtype=np.float32)


def ruido(a):
    """Desvio robusto; fundos quase constantes (PNG quantizado) têm MAD zero,
    então usa o desvio padrão da faixa central dos valores com piso de 1 nível."""
    lo, hi = np.percentile(a, [5, 95])
    meio = a[(a >= lo) & (a <= hi)]
    return max(float(meio.std()), 1.0)


def fila(workflow, n):
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


# --- notas -----------------------------------------------------------------
# Cada função recebe a lista de imagens do objeto e devolve (nota, motivo).

def nota_byw(imgs):
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
    yp, xp = np.unravel_index(np.argmax(pos), pos.shape)
    # o par negativo tem que estar perto (anã marrom anda poucos pixels)
    r = 150  # em ~10 anos uma anã marrom próxima anda >100px nesta escala
    janela = neg[max(0, yp - r):yp + r, max(0, xp - r):xp + r]
    yn, xn = np.unravel_index(np.argmax(janela), janela.shape)
    dist = np.hypot(yn + max(0, yp - r) - yp, xn + max(0, xp - r) - xp)
    forca = min(pos[yp, xp], janela[yn, xn])
    nota = float(forca) if dist > 4 else float(forca) * 0.3
    extra = {"pos": [int(xp), int(yp)], "lado": [int(d.shape[1]), int(d.shape[0])]}
    return nota, f"par claro/escuro de {forca:.1f}σ, deslocamento {dist:.0f}px em ({xp},{yp})", extra


def nota_aa(imgs):
    """Cauda: isola a mancha ligada ao objeto central e mede quanto o centro
    de luz dela se afasta do pico. Estrela ou rastro de movimento são
    simétricos; uma cauda ou coma puxa a luz para um lado. Parâmetros
    escolhidos por injeção de caudas sintéticas (testes/grade_aa.py)."""
    notas, motivos = [], []
    for i, p in enumerate(imgs):
        im = 255 - cinza(p)  # neste projeto as estrelas são escuras
        im = ndimage.gaussian_filter(im - np.median(im), 2)
        s = ruido(im)
        h, w = im.shape
        cy, cx = h // 2, w // 2
        rot, _ = ndimage.label(im > 1.5 * s)
        c = rot[cy - 6:cy + 7, cx - 6:cx + 7]
        ids = c[c > 0]
        if not ids.size:
            notas.append(0.0)  # alvo não aparece neste quadro
            continue
        alvo = rot == np.bincount(ids).argmax()
        area = alvo.sum()
        if area < 6 or area > 3000:
            notas.append(0.0)
            continue
        yy, xx = np.nonzero(alvo)
        pesos = im[yy, xx]
        k = np.argmax(pesos)
        desvio = np.hypot((pesos * yy).sum() / pesos.sum() - yy[k],
                          (pesos * xx).sum() / pesos.sum() - xx[k])
        # outro pico forte dentro da mancha = estrela grudada, não cauda
        picos = (im == ndimage.maximum_filter(im, 7)) & alvo & (im > 0.4 * pesos.max())
        grudada = picos.sum() > 1
        notas.append(float(desvio) * (0.2 if grudada else 1.0))
        motivos.append(f"q{i + 1} {desvio:.1f}px" + (" (estrela grudada)" if grudada else ""))
    if not motivos:
        return 0.0, "alvo não detectado"
    # mediana: cauda real aparece em todos os quadros, estrela grudada não
    return float(np.median(notas)), "luz deslocada do pico: " + ", ".join(motivos)


def nota_kn(imgs, meta):
    """Real ou bogus. Medido contra os 51 objetos de treino rotulados pela
    equipe (testes/treino_kn.py): o melhor sinal é a fonte aparecer no painel
    de ciência E no de diferença. Só o painel de diferença dava AUC 0.71;
    os dois juntos dão 0.84."""
    im = Image.open(imgs[0]).convert("L")
    W, H = im.size
    sx, sy = W / 900, H / 432  # o layout do triptico é fixo

    def pico(x0, x1):
        a = np.asarray(im.crop((int(x0 * sx), int(45 * sy), int(x1 * sx), int(333 * sy))), np.float32)
        h, w = a.shape
        c = ndimage.gaussian_filter(a, 1.5)[h // 2 - 12:h // 2 + 13, w // 2 - 12:w // 2 + 13]
        return max(0.0, float(c.max() - np.median(a)) / ruido(a))

    sci, dif = pico(8, 297), pico(604, 893)
    nota = float(np.log1p(sci) + np.log1p(dif))
    return nota, f"ciência {sci:.1f}σ, diferença {dif:.1f}σ, s2n {meta.get('s2n', '?')}, mag {meta.get('mag', '?')}"


def avaliar(chave, s):
    urls = [list(l.values())[0] for l in s["locations"]]
    imgs = [baixar(u) for u in urls]
    meta = s.get("metadata", {})
    extra = {}
    if chave == "byw":
        nota, motivo, extra = nota_byw(imgs)
    elif chave == "aa":
        nota, motivo = nota_aa(imgs)
    else:
        nota, motivo = nota_kn(imgs, meta)
    return dict(id=s["id"], urls=urls, nota=round(nota, 2), motivo=motivo, meta=meta, **extra)


# --- já é conhecido? ------------------------------------------------------

def ceu_byw(meta, xp, yp, largura=946, altura=946):
    """Pixel do recorte do Backyard Worlds -> RA/Dec (norte em cima, leste à esquerda).
    O FOV vem nos metadados como "118.25 x 101.75 arcseconds" (largura x altura)."""
    ra0, de0 = float(meta["RA"]), float(meta["DEC"])
    partes = str(meta.get("FOV", "118.25")).replace("x", " ").split()
    fov_x = float(partes[0])
    fov_y = float(partes[1]) if len(partes) > 1 and partes[1].replace(".", "", 1).isdigit() else fov_x
    dx = (xp - largura / 2) * fov_x / largura
    dy = (yp - altura / 2) * fov_y / altura
    return ra0 - dx / 3600 / np.cos(np.radians(de0)), de0 - dy / 3600


def catwise_movendo(ra, dec, raio=40):
    """Fontes do CatWISE2020 com movimento próprio > 0.05"/ano e > 5σ perto da posição."""
    url = ("https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=II/365/catwise"
           f"&-c={ra:.5f}%20{dec:+.5f}&-c.rs={raio}&-out=Name,pmRA,pmDE,e_pmRA,e_pmDE&-out.max=50")
    try:
        linhas = abrir(url, 30, tentativas=3).decode().splitlines()
    except Exception:
        return None  # sem resposta: não dá para afirmar nada
    achados = []
    for l in linhas:
        p = l.split("\t")
        if len(p) == 5 and p[0].startswith("J"):
            try:
                pm = float(np.hypot(float(p[1]), float(p[2])))
                erro = float(np.hypot(float(p[3]), float(p[4])))
            except ValueError:
                continue
            if pm > 0.05 and pm > 5 * erro:  # pm do CatWISE é ruidoso em fonte fraca
                achados.append((p[0].strip(), round(pm, 2)))
    return sorted(achados, key=lambda x: -x[1])


def gaia_movendo(ra, dec, raio=40):
    """Estrelas do Gaia DR3 com movimento próprio > 50 mas/ano perto da posição."""
    url = ("https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=I/355/gaiadr3"
           f"&-c={ra:.5f}%20{dec:+.5f}&-c.rs={raio}&-out=Source,pmRA,pmDE&-out.max=50")
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


def checar_conhecidos(itens, corte=6.0):
    """Só para os candidatos fortes do Backyard Worlds (consulta externa)."""
    for it in itens:
        if it["nota"] < corte or "pos" not in it or "RA" not in it["meta"]:
            continue
        ra, dec = ceu_byw(it["meta"], *it["pos"], *it.get("lado", (946, 946)))
        cw, ga = catwise_movendo(ra, dec), gaia_movendo(ra, dec)
        mov = sorted([("CWISE " + n, pm) for n, pm in cw or []] + (ga or []), key=lambda x: -x[1])
        it["ceu"] = (round(ra, 5), round(dec, 5))
        if mov:  # basta um catálogo achar algo se movendo
            it["conhecido"] = "já catalogado: " + ", ".join(f"{n} ({pm}\"/ano)" for n, pm in mov[:2])
        elif cw is None or ga is None:  # sem os dois não dá para dizer que é novo
            it["conhecido"] = "catálogo não respondeu"
        else:
            it["conhecido"] = "NADA no CatWISE/Gaia se movendo aqui — possível descoberta, confira no WiseView"
        time.sleep(0.5)


# --- relatório -------------------------------------------------------------

def relatorio(resultados):
    partes = ["""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>CacaZoo</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:-apple-system,system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:16px}
h2{margin-top:32px}.c{display:flex;gap:12px;align-items:center;background:#1c1c1c;border-radius:8px;padding:10px;margin:8px 0}
.c img{height:150px;border-radius:4px;background:#000}.n{font-size:28px;font-weight:700;min-width:70px;text-align:center}
a{color:#7cf}small{color:#999}.blink{position:relative}</style>
<h1>CacaZoo — melhores candidatos</h1>
<p><small>Nota = força do sinal automático. Abra os do topo, confira e classifique no Zooniverse. Se achar algo, comente no Talk para a equipe ver.</small></p>"""]
    for chave, (proj, itens) in resultados.items():
        partes.append(f"<h2>{html.escape(proj['nome'])} <small>— {proj['alvo']}</small></h2>")
        for it in sorted(itens, key=lambda x: -x["nota"]):
            base = f"https://www.zooniverse.org/projects/{proj['slug']}"
            imgs = it["urls"]
            if chave == "byw":
                mostra = [imgs[0], imgs[-1]]
            elif chave == "aa":
                mostra = imgs[:5]
            else:
                mostra = imgs[:1]
            tags = "".join(f'<img src="{html.escape(u)}" loading="lazy">' for u in mostra)
            partes.append(
                f'<div class="c"><div class="n">{it["nota"]}</div><div>{tags}<br>'
                f'<small>#{it["id"]} · {html.escape(it["motivo"])}</small><br>'
                + (f'<b>{html.escape(it["conhecido"])}</b> <small>RA {it["ceu"][0]} Dec {it["ceu"][1]}</small><br>' if it.get("conhecido") else "") +
                f'<a href="{base}/classify/workflow/{proj["workflow"]}/subject/{it["id"]}" target="_blank">classificar</a> · '
                f'<a href="{base}/talk/subjects/{it["id"]}" target="_blank">Talk</a></div></div>')
    return "\n".join(partes)


def main():
    ap = argparse.ArgumentParser(description="Triagem de objetos do Zooniverse (Backyard Worlds, Active Asteroids, Kilonova Seekers).")
    ap.add_argument("--n", type=int, default=40, help="objetos por projeto")
    ap.add_argument("--projeto", choices=list(PROJETOS), action="append")
    ap.add_argument("--reusar", action="store_true", help="reavalia os objetos do último resultados.json (cache local)")
    args = ap.parse_args()
    caminho = os.path.join(AQUI, "resultados.json")
    anteriores = {}
    if args.reusar:
        for chave, itens in ler_json(caminho, {}).items():
            anteriores[chave] = [dict(id=i["id"], metadata=i["meta"],
                                      locations=[{"image/png": u} for u in i["urls"]]) for i in itens]
    resultados = {}
    for chave in args.projeto or list(PROJETOS):
        proj = PROJETOS[chave]
        print(f"{proj['nome']}: buscando {args.n} objetos…", file=sys.stderr)
        if args.reusar and chave not in anteriores:
            print("  nada salvo deste projeto para reusar; pulando", file=sys.stderr)
            continue
        subs = anteriores[chave] if args.reusar else fila(proj["workflow"], args.n)
        with ThreadPoolExecutor(8) as ex:
            itens = []
            for s, r in zip(subs, ex.map(lambda s: _seguro(chave, s), subs)):
                if r:
                    itens.append(r)
        if chave == "byw":
            checar_conhecidos(itens)
        resultados[chave] = (proj, itens)
        top = sorted(itens, key=lambda x: -x["nota"])[:3]
        for it in top:
            print(f"  {it['nota']:6.2f}  #{it['id']}  {it['motivo']}  {it.get('conhecido', '')}", file=sys.stderr)
    # rodada parcial (--projeto) mantém os outros projetos do último resultado
    for chave, itens in ler_json(caminho, {}).items():
        if chave not in resultados and chave in PROJETOS:
            resultados[chave] = (PROJETOS[chave], itens)
    gravar(os.path.join(AQUI, "report.html"), relatorio(resultados).encode())
    gravar_json(caminho, {k: v[1] for k, v in resultados.items()}, ensure_ascii=False, indent=1)
    print(os.path.join(AQUI, "report.html"))


def _seguro(chave, s):
    try:
        return avaliar(chave, s)
    except Exception as e:  # um objeto quebrado não derruba a rodada
        print(f"  erro em #{s.get('id')}: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    main()
