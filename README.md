# Colli Finance API

API de finanzas personales construida con FastAPI, SQLAlchemy y PostgreSQL. Incluye autenticación basada en JWT, auditoría y registros estructurados en JSON compatibles con Loki.

## Requisitos

- Python 3.11+
- PostgreSQL 13+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Cree un archivo `.env` (se incluye un ejemplo en el repositorio) y configure las variables necesarias para su entorno, incluyendo las URLs de las bases de datos de desarrollo y producción.

## Ejecución

```bash
uvicorn app.main:app --reload
```

En el arranque la aplicación:

1. Crea la base de datos si no existe.
2. Ejecuta las migraciones de Alembic (`MIGRATE_ON_START=true`).
3. Opcionalmente reinicia el esquema (`RESET_DB_ON_START=true`).
4. Inserta las categorías predeterminadas.

## Endpoints principales

- `GET /health`: verificación de estado.
- `POST /auth/login`: autenticación mediante número de teléfono y contraseña.
- `POST /users`: registro de usuarios.
- `POST /habitos/registrar`: registra hábitos asociados al usuario autenticado (auditable).
- CRUD completo para usuarios, categorías, tarjetas y transacciones.
- `GET /summary/cards`: resumen de saldos por tarjeta para un rango de fechas.
- `GET /audit`: consulta de registros de auditoría del usuario.

Los logs se emiten en formato JSON con campos unificados y se envían a Loki cuando `LOKI_URL` está configurado.

## Ejecución con Docker

1. Copie el archivo `.env.example` a `.env` y ajuste los valores según su entorno.
2. Construya y levante los servicios con la imagen local:

   ```bash
   docker compose -f docker-compose.local.yml up --build
   ```

   La API quedará disponible en `http://localhost:8000` y la base de datos en el puerto `5432`.

3. Si ya cuenta con una imagen publicada en Docker Hub, puede ejecutarla con:

   ```bash
   docker compose -f docker-compose.dockerhub.yml up
   ```

   Sustituya `your-dockerhub-user/colli-finance-api:latest` por la referencia de su imagen.

Ambos archivos de Compose incluyen servicios para PostgreSQL y Loki, y cargan automáticamente las variables del archivo `.env`.
