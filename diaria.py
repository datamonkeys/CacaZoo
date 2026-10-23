#!/usr/bin/env python3
"""Varredura diária do CacaZoo (roda pelo launchd).

Varre o Backyard Worlds, compara com os candidatos já avisados e manda uma
notificação do macOS só quando aparece um candidato forte que não está no
CatWISE nem no Gaia. Os demais projetos entram no relatório sem aviso.
"""
import json, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
VISTOS = os.path.join(AQUI, "avisados.json")
LOG = os.path.join(AQUI, "diaria.log")
# movers reais vistos nas varreduras deram 8–40; ruído fica em 6–7
AVISO = 8.0


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M ") + msg + "\n")


def avisar(titulo, texto):
    script = f'display notification {json.dumps(texto)} with title {json.dumps(titulo)} sound name "Glass"'
    subprocess.run(["osascript", "-e", script], check=False)


def limpar_cache(dias=3):
    cache = os.path.join(AQUI, "cache")
    limite = time.time() - dias * 86400
    for nome in os.listdir(cache) if os.path.isdir(cache) else []:
        p = os.path.join(cache, nome)
        if nome.endswith(".png") and os.path.getmtime(p) < limite:
            os.remove(p)


def main():
    limpar_cache()
    r = subprocess.run([sys.executable, os.path.join(AQUI, "caca.py"), "--n", "500", "--projeto", "byw"],
                       capture_output=True, text=True, cwd=AQUI)
    if r.returncode:
        log("falhou: " + r.stderr[-500:])
        avisar("CacaZoo", "A varredura diária falhou — veja diaria.log")
        return
    subprocess.run([sys.executable, os.path.join(AQUI, "caca.py"), "--n", "100", "--projeto", "aa", "--projeto", "kn"],
                   capture_output=True, cwd=AQUI)

    itens = json.load(open(os.path.join(AQUI, "resultados.json")))["byw"]
    vistos = set(json.load(open(VISTOS))) if os.path.exists(VISTOS) else set()
    novos = [i for i in itens if i.get("conhecido", "").startswith("NADA") and i["nota"] >= AVISO and i["id"] not in vistos]
    fortes = sum(1 for i in itens if i.get("conhecido"))
    log(f"{len(itens)} objetos, {fortes} fortes, {len(novos)} possíveis descobertas novas")
    if novos:
        vistos.update(i["id"] for i in novos)
        json.dump(sorted(vistos), open(VISTOS, "w"))
        melhor = max(novos, key=lambda i: i["nota"])
        avisar("CacaZoo: possível descoberta!",
               f"{len(novos)} candidato(s) fora dos catálogos. Melhor: #{melhor['id']} nota {melhor['nota']}")
        subprocess.run(["open", os.path.join(AQUI, "report.html")])


if __name__ == "__main__":
    main()
