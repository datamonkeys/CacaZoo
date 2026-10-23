# Rodada do CacaZoo em qualquer máquina (Linux):
#   docker build -t cacazoo .
#   docker run --rm -v "$PWD/saida:/saida" cacazoo --n 40
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY caca_zoo ./caca_zoo
RUN uv sync --locked --no-dev --extra sentry
ENV PATH="/app/.venv/bin:$PATH" CACAZOO_SAIDA=/saida
RUN mkdir -p /saida
ENTRYPOINT ["python", "-m", "caca_zoo"]
