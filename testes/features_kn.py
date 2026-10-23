import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import caca

def paineis(p):
    im = Image.open(p).convert("L"); W, H = im.size; sx, sy = W / 900, H / 432
    cut = lambda x0, x1: np.asarray(im.crop((int(x0 * sx), int(45 * sy), int(x1 * sx), int(333 * sy))), np.float32)
    return cut(8, 297), cut(306, 595), cut(604, 893)

def feats(p, meta):
    sci, ref, dif = paineis(p)
    out = {}
    for nome, a in (("dif", dif), ("sci", sci), ("ref", ref)):
        h, w = a.shape; s = caca.ruido(a); b = np.median(a)
        c = ndimage.gaussian_filter(a, 1.5)[h//2-12:h//2+13, w//2-12:w//2+13] - b
        out[nome + "_pico"] = c.max() / s
        out[nome + "_buraco"] = -c.min() / s
        if nome == "dif":
            # simetria: ponto real é redondo; resíduo de subtração tem estrutura
            out["dif_assim"] = np.abs(c - c[::-1, ::-1]).sum() / (np.abs(c).sum() + 1e-6)
            # compacidade: fração do fluxo positivo no miolo
            pos = np.clip(c, 0, None)
            out["dif_compacto"] = pos[9:16, 9:16].sum() / (pos.sum() + 1e-6)
            out["dif_central"] = c[12, 12] / (c.max() + 1e-6)
    out["ref_razao"] = out["ref_pico"] / (out["sci_pico"] + 1)  # estrela brilhante no ref = sobra de subtração
    out["s2n"] = float(meta.get("s2n") or 0)
    out["mag"] = float(meta.get("mag") or 0)
    return out

from _dados import treino_kn
subs = treino_kn()
X, y = [], []
for s in subs:
    p = caca.baixar(list(s["locations"][0].values())[0])
    X.append(feats(p, s["metadata"])); y.append(s["metadata"].get("#feedback_1_answer") == "0")
y = np.array(y)
def auc(v):
    p, n = v[y], v[~y]; return np.mean([(a > b) + 0.5 * (a == b) for a in p for b in n])
for k in X[0]:
    v = np.array([x[k] for x in X]); a = auc(v)
    print(f"{k:14s} AUC {max(a, 1-a):.2f} {'(maior=real)' if a >= .5 else '(menor=real)'}")
caca.gravar_json(os.path.join(caca.CACHE, "kn_feats.json"), {"X": [{k: float(v) for k, v in x.items()} for x in X], "y": y.tolist()})
