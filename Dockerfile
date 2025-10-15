# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ARG USER_ID=1000
ARG GROUP_ID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root con UID/GID provistos (para que coincida con el host y evitar problemas de permisos)
RUN groupadd -g ${GROUP_ID} appuser \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -r appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Copiar y dar permisos al entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Cambiar permisos al usuario
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000","--log-level","debug","--access-log"]