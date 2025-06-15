FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /src/phice
COPY pyproject.toml .
RUN uv sync
RUN uv pip install gunicorn

COPY src ./src
COPY app.py .

CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]
