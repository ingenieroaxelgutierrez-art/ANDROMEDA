# ============================================================
# ANDROMEDA — Backend (Python 3.11 + FastAPI)
# Imagen de desarrollo: código montado como volumen (hot reload)
# ============================================================

FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema necesarias para algunos paquetes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (capa cacheada — solo se reconstruye si cambia requirements.txt)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Descargar modelo spaCy en español
RUN python -m spacy download es_core_news_sm || true

# En desarrollo el código se monta como volumen (no se copia aquí)
# En producción (compose.prod.yml) se hace COPY . .

EXPOSE 8000

# Uvicorn con --reload para hot reload en desarrollo
CMD ["uvicorn", "app.api.main_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
