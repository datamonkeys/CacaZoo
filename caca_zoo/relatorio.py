"""report.html com os candidatos ordenados e os links para classificar."""

from __future__ import annotations

import html
from typing import Any

CABECALHO = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>CacaZoo</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:-apple-system,system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:16px}
h2{margin-top:32px}
.c{display:flex;gap:12px;align-items:center;background:#1c1c1c;border-radius:8px;padding:10px;margin:8px 0}
.c img{height:150px;border-radius:4px;background:#000}
.n{font-size:28px;font-weight:700;min-width:70px;text-align:center}a{color:#7cf}small{color:#999}</style>
<h1>CacaZoo — melhores candidatos</h1>
<p><small>Nota = força do sinal automático. Abra os do topo, confira e classifique no Zooniverse.
Se achar algo, comente no Talk para a equipe ver.</small></p>"""


def imagens_mostradas(chave: str, urls: list[str]) -> list[str]:
    """Backyard Worlds: primeira e última época; Active Asteroids: os 5 quadros; Kilonova: o tríptico."""
    if chave == "byw":
        return [urls[0], urls[-1]] if urls else []
    return urls[:5] if chave == "aa" else urls[:1]


def cartao(chave: str, proj: dict[str, Any], it: dict[str, Any]) -> str:
    base = f"https://www.zooniverse.org/projects/{proj['slug']}"
    tags = "".join(f'<img src="{html.escape(u)}" loading="lazy">' for u in imagens_mostradas(chave, it["urls"]))
    catalogo = ""
    if it.get("conhecido"):
        ceu = it.get("ceu")
        onde = f" <small>RA {ceu[0]} Dec {ceu[1]}</small>" if ceu else ""
        catalogo = f"<b>{html.escape(it['conhecido'])}</b>{onde}<br>"
    classificar = f"{base}/classify/workflow/{proj['workflow']}/subject/{it['id']}"
    return (
        f'<div class="c"><div class="n">{it["nota"]}</div><div>{tags}<br>'
        f"<small>#{it['id']} · {html.escape(it['motivo'])}</small><br>{catalogo}"
        f'<a href="{classificar}" target="_blank">classificar</a> · '
        f'<a href="{base}/talk/subjects/{it["id"]}" target="_blank">Talk</a></div></div>'
    )


def relatorio(resultados: dict[str, Any]) -> str:
    partes = [CABECALHO]
    for chave, (proj, itens) in resultados.items():
        partes.append(f"<h2>{html.escape(proj['nome'])} <small>— {proj['alvo']}</small></h2>")
        partes += [cartao(chave, proj, it) for it in sorted(itens, key=lambda x: -x["nota"])]
    return "\n".join(partes)
