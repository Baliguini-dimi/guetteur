FROM python:3.12.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && \
    useradd --system --uid 10001 --create-home guetteur

USER guetteur
EXPOSE 8000
CMD ["uvicorn", "guetteur.main:app", "--host", "0.0.0.0", "--port", "8000"]
