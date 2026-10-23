"""Linha de comando: varre os projetos, grava resultados.json e report.html."""

from __future__ import annotations

import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from . import registro
from .catalogos import checar_conhecidos
from .rede import PASTA, gravar, gravar_json, ler_json
from .relatorio import relatorio
from .zooniverse import PROJETOS, _seguro, fila


def _salvos(caminho: str) -> dict[str, list[dict[str, Any]]]:
    """Objetos da última rodada no formato da API, para --reusar."""
    return {
        chave: [dict(id=i["id"], metadata=i["meta"], locations=[{"image/png": u} for u in i["urls"]]) for i in itens]
        for chave, itens in ler_json(caminho, {}).items()
    }


def rodar(n: int, projetos: list[str], reusar: bool, pasta: str = PASTA) -> dict[str, Any]:
    log = registro.obter()
    caminho = os.path.join(pasta, "resultados.json")
    anteriores = _salvos(caminho) if reusar else {}
    resultados: dict[str, Any] = {}
    for chave in projetos:
        proj = PROJETOS[chave]
        if reusar and chave not in anteriores:
            log.warning("nada_para_reusar", projeto=chave)
            continue
        subs = anteriores[chave] if reusar else fila(proj["workflow"], n)
        with ThreadPoolExecutor(8) as ex:
            itens = [r for r in ex.map(lambda s, c=chave: _seguro(c, s), subs) if r]
        if chave == "byw":
            checar_conhecidos(itens)
        resultados[chave] = (proj, itens)
        top = sorted(itens, key=lambda x: -x["nota"])[:3]
        log.info(
            "projeto",
            projeto=chave,
            objetos=len(subs),
            avaliados=len(itens),
            top=[[it["id"], it["nota"], it.get("conhecido", "")] for it in top],
        )
    # rodada parcial (--projeto) mantém os outros projetos do último resultado
    for chave, itens in ler_json(caminho, {}).items():
        if chave not in resultados and chave in PROJETOS:
            resultados[chave] = (PROJETOS[chave], itens)
    gravar(os.path.join(pasta, "report.html"), relatorio(resultados).encode())
    gravar_json(caminho, {k: v[1] for k, v in resultados.items()}, ensure_ascii=False, indent=1)
    return resultados


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="cacazoo",
        description="Triagem de objetos do Zooniverse (Backyard Worlds, Active Asteroids, Kilonova Seekers).",
    )
    ap.add_argument("--n", type=int, default=40, help="objetos por projeto")
    ap.add_argument("--projeto", choices=list(PROJETOS), action="append")
    ap.add_argument("--reusar", action="store_true", help="reavalia os objetos do último resultados.json (cache local)")
    args = ap.parse_args(argv)
    registro.configurar(os.path.join(PASTA, "cacazoo.log"))
    try:
        rodar(args.n, args.projeto or list(PROJETOS), args.reusar)
    except Exception as e:
        registro.obter().error("rodada_falhou", erro=repr(e))
        raise
    print(os.path.join(PASTA, "report.html"))
    return 0
