"""Varredura diária (pensada para rodar agendada, ex.: launchd/cron).

Varre o Backyard Worlds, compara com os candidatos já avisados e notifica só
quando aparece um candidato forte que não está no CatWISE nem no Gaia. Os
demais projetos entram no relatório sem aviso. A notificação usa o macOS; em
outros sistemas o aviso vai para o log."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from . import registro
from .cli import rodar
from .rede import CACHE, PASTA, gravar_json, ler_json

VISTOS = os.path.join(PASTA, "avisados.json")
# movers reais vistos nas varreduras deram 8–40; ruído fica em 6–7
AVISO = 8.0


def avisar(titulo: str, texto: str, abrir_relatorio: bool = False) -> None:
    registro.obter().warning("alerta", titulo=titulo, texto=texto)
    if sys.platform == "darwin":
        script = f'display notification {json.dumps(texto)} with title {json.dumps(titulo)} sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False)
        if abrir_relatorio:
            subprocess.run(["open", os.path.join(PASTA, "report.html")], check=False)


def limpar_cache(dias: int = 3) -> None:
    limite = time.time() - dias * 86400
    if not os.path.isdir(CACHE):
        return
    for nome in os.listdir(CACHE):
        p = os.path.join(CACHE, nome)
        if nome.endswith((".png", ".tmp")) and os.path.getmtime(p) < limite:
            os.remove(p)


def etapa(n: int, projetos: list[str]) -> bool:
    try:
        rodar(n, projetos, reusar=False)
        return True
    except Exception as e:
        registro.obter().error("etapa_falhou", projetos=projetos, erro=repr(e))
        return False


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(
        prog="cacazoo-diaria",
        description="Varredura diária: 500 do Backyard Worlds + 100 do Active Asteroids/Kilonova, "
        f"aviso só para candidato fora dos catálogos com nota >= {AVISO}.",
    ).parse_args(argv)
    registro.configurar(os.path.join(PASTA, "diaria.log"))
    limpar_cache()
    if not etapa(500, ["byw"]):
        avisar("CacaZoo", "A varredura diária falhou — veja diaria.log")
        return 1
    if not etapa(100, ["aa", "kn"]):
        avisar("CacaZoo", "Active Asteroids/Kilonova falhou — veja diaria.log")

    itens = ler_json(os.path.join(PASTA, "resultados.json"), {}).get("byw", [])
    vistos = set(ler_json(VISTOS, []))
    novos = [i for i in itens if i.get("conhecido", "").startswith("NADA") and i["nota"] >= AVISO and i["id"] not in vistos]
    registro.obter().info(
        "diaria", objetos=len(itens), fortes=sum(1 for i in itens if i.get("conhecido")), possiveis_descobertas=len(novos)
    )
    if novos:
        vistos.update(i["id"] for i in novos)
        gravar_json(VISTOS, sorted(vistos))
        melhor = max(novos, key=lambda i: i["nota"])
        avisar(
            "CacaZoo: possível descoberta!",
            f"{len(novos)} candidato(s) fora dos catálogos. Melhor: #{melhor['id']} nota {melhor['nota']}",
            abrir_relatorio=True,
        )
    return 0
