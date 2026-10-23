"""HTTP com novas tentativas, cache de imagens e gravação que não corrompe."""

from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.request
from typing import Any

from . import __version__

REPO = "https://github.com/louisperner/CacaZoo"
HDR = {"Accept": "application/vnd.api+json; version=1", "User-Agent": f"CacaZoo/{__version__} (+{REPO})"}
# resultados, relatório, log e cache: ao lado do programa, ou CACAZOO_SAIDA (ex.: Docker)
PASTA = os.environ.get("CACAZOO_SAIDA") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(PASTA, "cache")


def abrir(url: str, timeout: float, tentativas: int = 4) -> bytes:
    """Conteúdo da URL, com novas tentativas e espera crescente (1, 2, 4 s)."""
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(2**i)
    raise ValueError("tentativas precisa ser >= 1")


def get_json(url: str) -> Any:
    return json.loads(abrir(url, 30))


def gravar(caminho: str, dados: bytes) -> None:
    """Grava num temporário e troca no fim: crash ou dois threads no mesmo
    arquivo nunca deixam um arquivo pela metade no lugar."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(caminho), suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(dados)
    os.replace(tmp, caminho)


def gravar_json(caminho: str, obj: Any, **kw: Any) -> None:
    gravar(caminho, json.dumps(obj, **kw).encode())


def ler_json(caminho: str, padrao: Any) -> Any:
    try:
        with open(caminho) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def baixar(url: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, url.rsplit("/", 1)[-1])
    if not os.path.exists(caminho):
        gravar(caminho, abrir(url, 60))
    return caminho
