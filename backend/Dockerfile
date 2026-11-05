# python:3.12.9-slim
FROM python@sha256:f17ec845ebdd4f3347431579e1c22eaeec82913f039f2a54b937c7ff870bacdb

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN useradd --system --uid 10001 --create-home guetteur

COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes --no-deps -r requirements.lock

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

COPY alembic.ini ./
COPY migrations ./migrations

USER guetteur
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
CMD ["uvicorn", "guetteur.main:app", "--host", "0.0.0.0", "--port", "8000"]
