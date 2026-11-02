# Imagen unica para entrenamiento y API.
# Usar la misma imagen garantiza que las versiones de librerias y el preprocesador
# sean exactamente identicos al entrenar y al servir.

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias primero para aprovechar cache de capas Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

# Codigo fuente y configuracion
COPY params.yaml ./
COPY data ./data
COPY src ./src
COPY api ./api

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Imagen para desarrollo, pruebas con pytest y notebooks
FROM runtime AS dev

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY tests ./tests
COPY notebooks ./notebooks

CMD ["pytest", "-q"]
