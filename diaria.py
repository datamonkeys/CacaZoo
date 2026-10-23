#!/usr/bin/env python3
"""Varredura diária do CacaZoo (pensada para rodar agendada, ex.: launchd/cron).

Varre o Backyard Worlds, compara com os candidatos já avisados e manda uma
notificação só quando aparece um candidato forte que não está no CatWISE nem
no Gaia. Os demais projetos entram no relatório sem aviso.
A notificação usa o macOS; em outros sistemas o aviso vai para o terminal/log.
"""
import os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import caca

VISTOS = os.path.join(AQUI, "avisados.json")
LOG = os.path.join(AQUI, "diaria.log")
# movers reais vistos nas varreduras deram 8–40; ruído fica em 6–7
AVISO = 8.0


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M ") + msg + "\n")


def avisar(titulo, texto, abrir_relatorio=False):
    if sys.platform == "darwin":
        script = f'display notification {caca.json.dumps(texto)} with title {caca.json.dumps(titulo)} sound name "Glass"'
        subprocess.run(["osascript", "-e", script], check=False)
        if abrir_relatorio:
            subprocess.run(["open", os.path.join(AQUI, "report.html")], check=False)
    else:
        print(f"*** {titulo}: {texto}", file=sys.stderr)


def limpar_cache(dias=3):
    limite = time.time() - dias * 86400
    if not os.path.isdir(caca.CACHE):
        return
    for nome in os.listdir(caca.CACHE):
        p = os.path.join(caca.CACHE, nome)
        if nome.endswith((".png", ".tmp")) and os.path.getmtime(p) < limite:
            os.remove(p)


def rodar(*args):
    r = subprocess.run([sys.executable, os.path.join(AQUI, "caca.py"), *args],
                       capture_output=True, text=True, cwd=AQUI)
    if r.returncode:
        log(f"falhou ({' '.join(args)}): " + r.stderr[-500:].replace("\n", " | "))
    return r.returncode == 0


def main():
    limpar_cache()
    if not rodar("--n", "500", "--projeto", "byw"):
        avisar("CacaZoo", "A varredura diária falhou — veja diaria.log")
        return
    if not rodar("--n", "100", "--projeto", "aa", "--projeto", "kn"):
        avisar("CacaZoo", "Active Asteroids/Kilonova falhou — veja diaria.log")

    itens = caca.ler_json(os.path.join(AQUI, "resultados.json"), {}).get("byw", [])
    vistos = set(caca.ler_json(VISTOS, []))
    novos = [i for i in itens if i.get("conhecido", "").startswith("NADA") and i["nota"] >= AVISO and i["id"] not in vistos]
    fortes = sum(1 for i in itens if i.get("conhecido"))
    log(f"{len(itens)} objetos, {fortes} fortes, {len(novos)} possíveis descobertas novas")
    if novos:
        vistos.update(i["id"] for i in novos)
        caca.gravar_json(VISTOS, sorted(vistos))
        melhor = max(novos, key=lambda i: i["nota"])
        avisar("CacaZoo: possível descoberta!",
               f"{len(novos)} candidato(s) fora dos catálogos. Melhor: #{melhor['id']} nota {melhor['nota']}",
               abrir_relatorio=True)


if __name__ == "__main__":
    main()
