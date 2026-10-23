# CacaZoo

[![ci](https://github.com/louisperner/CacaZoo/actions/workflows/ci.yml/badge.svg)](https://github.com/louisperner/CacaZoo/actions/workflows/ci.yml)

Automatic triage for three [Zooniverse](https://www.zooniverse.org) projects where volunteers get
discovery credit: **Backyard Worlds: Cool Neighbors** (moving brown dwarfs), **Active Asteroids**
(asteroids with a tail or coma) and **Kilonova Seekers** (real transients). It pulls the subjects
currently in each project's queue through the public Panoptes API, scores every subject by image
analysis, and writes `report.html` ranked best-first, with links to classify and to Talk.
**Classifying is still done by you, on the Zooniverse site.** *Português abaixo.*

## Install and run

    uv sync                              # or: pip install .   (Python 3.9+: numpy, scipy, Pillow, structlog)
    uv run cacazoo --n 40                # 40 subjects per project
    uv run cacazoo --n 300 --projeto byw
    uv run cacazoo --reusar              # rescore the last run from the local cache
    open report.html

`python -m caca_zoo` and `python3 caca.py` do the same. With Docker:

    docker build -t cacazoo .
    docker run --rm -v "$PWD/saida:/saida" cacazoo --n 40     # results land in ./saida

Each run writes `resultados.json`, `report.html` and one JSON line per event to `cacazoo.log`, next
to the program or in `$CACAZOO_SAIDA` if set. No API key is needed.

For strong Backyard Worlds candidates (score ≥ 6) the pixel is converted to RA/Dec and checked
against CatWISE2020 (proper motion > 0.05"/yr at > 5σ) and Gaia DR3 (> 50 mas/yr) on VizieR.
"NADA … se movendo aqui" means no known moving object there — open it in WiseView and post on Talk.

## Detectors and how they were validated (2026-10-22/23)

| Project | Detector | Validation |
|---|---|---|
| Backyard Worlds | median of the first third of the ~14 epochs vs. the last third; bright/dark pair; stars present in most epochs and stationary saturated stars masked | synthetic movers injected into 300 real subjects: 80 / 71 / 58 % recovered (faint / medium / bright) above the 95th percentile of clean subjects (`validacao/injecao_byw.py`, ~7 min) |
| Active Asteroids | light-centroid offset of the central blob, penalty for a blended second peak, median over the frames | synthetic tails: 37 / 58 / 66 % (faint / medium / strong) |
| Kilonova Seekers | log(peak in science panel) + log(peak in difference panel) | AUC 0.84 on the team's 51 labelled training subjects (the project's own s2n alone: 0.59) |

In a 1,500-subject Backyard Worlds scan, 29 of 32 strong candidates were real, already-catalogued
movers (e.g. CWISE J100733.72-455515.8 at 1.96"/yr); the rest were artefacts.

Re-run the validations (they use real images from a previous run):

    python -m validacao.injecao_byw    # needs: cacazoo --n 300 --projeto byw
    python -m validacao.injecao_aa     # needs: cacazoo --n 100 --projeto aa
    python -m validacao.treino_kn      # downloads the labelled training set on first use

### Known limitation

The main source of false alarms left in Backyard Worlds is the halo of a very bright, saturated
star whose core changes colour between epochs (seen on 2026-10-23: #122666059, score 8.5). Two
candidate rules (stationary halo brightness, distance to the saturated star) were tested and did not
separate these from real movers — catalogued movers also sit next to bright stars — so the detector
was left as is: a false alarm is cheaper than a missed mover. When an alert arrives, check first
whether the pair sits on the edge of a big saturated star.

## Daily run

`cacazoo-diaria` (or `python3 diaria.py`) scans 500 Backyard Worlds + 100 Active Asteroids/Kilonova
subjects, removes cached images older than 3 days, logs to `diaria.log`, and raises a desktop notification
(macOS `osascript`; printed elsewhere) only for a new uncatalogued candidate with score ≥ 8
(real movers scored 8–40, noise 6–7). Schedule it with launchd or cron. Set `SENTRY_DSN`
(and `pip install ".[sentry]"`) to get failures of scheduled runs in Sentry.

## Development

    uv sync --all-extras
    uv run python -m unittest discover -s tests -t .   # offline: synthetic images, APIs mocked
    uv run ruff check . && uv run mypy

Code layout: `caca_zoo/detectores.py` (the three detectors), `zooniverse.py` (projects, queue),
`catalogos.py` (pixel → sky, CatWISE, Gaia), `relatorio.py`, `rede.py` (HTTP with retries, cache,
atomic writes), `registro.py` (logging), `cli.py`, `diaria.py`. See `CONTRIBUTING.md` and `CHANGELOG.md`.

## Being polite to the APIs

One User-Agent with this repo's URL; retries with 1/2/4 s backoff; 0.3 s between queue pages and
0.5 s between VizieR lookups. A 500-subject run is ~100 queue requests and a few thousand small PNGs.

---

## Português

Triagem automática de três projetos do Zooniverse que dão crédito de descoberta. Baixa os objetos
na fila pela API pública, dá uma nota por análise de imagem e gera `report.html` ordenado, com links
para classificar e para o Talk. A classificação continua sendo sua, no site.

- `uv sync` (ou `pip install .`) e `uv run cacazoo --n 40` (ou `python3 caca.py --n 40`).
- Candidatos fortes do Backyard Worlds são conferidos no CatWISE e no Gaia: "NADA se movendo aqui"
  é o que vale abrir no WiseView e postar no Talk.
- Validação dos detectores na tabela acima (`validacao/`); testes offline em `tests/`.
- `cacazoo-diaria` / `diaria.py` é a varredura diária com aviso (notificação no macOS).

## License

MIT — see `LICENSE`.
