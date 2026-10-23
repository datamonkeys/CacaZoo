# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2026-10-23

### Adicionado
- Pacote `caca_zoo` (`python -m caca_zoo`, comandos `cacazoo` e `cacazoo-diaria`); `caca.py` e `diaria.py` continuam como lançadores.
- Log estruturado em JSON (structlog; cai no `logging` padrão se não estiver instalado) e Sentry opcional via `SENTRY_DSN`.
- Pasta de saída configurável (`CACAZOO_SAIDA`), Dockerfile, devcontainer, `.env.example`.
- CI (testes em 3.9 e 3.12, ruff, mypy, pip-audit, build do Docker), release por tag, Dependabot, `uv.lock`.
- Testes por módulo em `tests/` (imagens sintéticas, APIs simuladas); validações com dados reais em `validacao/`.

### Corrigido
- Relatório quebrava com candidato marcado no catálogo sem posição no céu.

### Removido
- `testes/grade_aa.py` e `testes/features_kn.py`: buscas exploratórias já concluídas
  (parâmetros do Active Asteroids e a escolha ciência + diferença no Kilonova).

## [0.2.0] - 2026-10-23

### Adicionado
- Checagem de candidatos fortes do Backyard Worlds no CatWISE2020 e no Gaia DR3.
- Varredura diária com aviso só para candidato forte fora dos catálogos.
- Testes offline e validações por injeção (Backyard Worlds, Active Asteroids) e pelo conjunto de treino (Kilonova).

### Corrigido
- Catálogo parcialmente fora do ar não vira mais "possível descoberta" (alarme falso).
- Cache de imagens e JSON gravados de forma atômica; novas tentativas com espera crescente.
- Posição do candidato guardada num campo (antes era lida de volta do texto do motivo); FOV retangular.
- `--reusar` sem o projeto salvo; a varredura diária detecta falha do Active Asteroids/Kilonova.
- Estrelas saturadas paradas mascaradas sem esconder movers brilhantes.

## [0.1.0] - 2026-10-22

### Adicionado
- Primeira versão: fila de três projetos do Zooniverse, detectores por análise de imagem, `report.html`.
