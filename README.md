# Colli Finance API

API de finanzas personales construida con FastAPI, SQLAlchemy y PostgreSQL para gestionar de manera integral tus finanzas personales. La aplicación proporciona un sistema completo de gestión financiera con autenticación JWT, auditoría de acciones, registro estructurado de logs y soporte para múltiples bancos y tarjetas.

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Características Principales](#características-principales)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Base de Datos](#base-de-datos)
- [API Endpoints](#api-endpoints)
- [Autenticación y Seguridad](#autenticación-y-seguridad)
- [Adjuntos y Carga de Archivos](#adjuntos-y-carga-de-archivos)
- [Logging y Monitoreo](#logging-y-monitoreo)
- [Docker](#docker)
- [Testing](#testing)
- [Desarrollo](#desarrollo)

## 📖 Descripción del Proyecto

Colli Finance es una API REST completa para la gestión de finanzas personales que permite a los usuarios:

- **Gestionar múltiples tarjetas bancarias**: Soporte para tarjetas de débito y crédito de diferentes bancos
- **Registrar transacciones**: Control detallado de ingresos y gastos con categorización
- **Realizar transferencias**: Movimientos entre tarjetas propias con registro automático
- **Adjuntar comprobantes**: Carga de archivos (imágenes, PDFs) asociados a transacciones
- **Generar reportes**: Resúmenes financieros por tarjeta y período
- **Auditar acciones**: Registro completo de todas las operaciones realizadas
- **Categorizar gastos**: Sistema de categorías predefinidas y personalizables

## ✨ Características Principales

### Gestión de Usuarios
- Registro y autenticación de usuarios con JWT
- Soporte para login con correo electrónico o número de teléfono
- Perfil de usuario con información personal
- Auditoría completa de acciones del usuario

### Gestión de Tarjetas
- Soporte para múltiples bancos configurables (Banregio, Banorte, Santander, HeyBanco, etc.)
- Tarjetas de débito y crédito con validaciones específicas
- Cálculo automático de saldos disponibles
- Sincronización automática de información bancaria mediante triggers
- Límite de crédito y seguimiento de utilización

### Transacciones
- Registro de ingresos y gastos
- Fecha de operación obligatoria para precisión histórica
- Categorización de transacciones
- Adjuntos de comprobantes (imágenes, PDFs)
- Marcado de transacciones ejecutadas vs. pendientes

### Transferencias
- Transferencias entre tarjetas propias
- Validación automática de saldos
- Registro doble (egreso en origen, ingreso en destino)
- Vinculación de comprobantes
- Categorización opcional

### Reportes y Resúmenes
- Resumen de saldos por tarjeta en rango de fechas
- Agregaciones de ingresos, gastos y saldos
- Consulta de auditoría de acciones

### Auditoría
- Registro automático de todas las operaciones críticas
- Consulta histórica de acciones por usuario
- Detalles completos de cada acción (recursos, cambios, timestamps)

### Email Listener Service (Nuevo)
- Monitoreo automático de correos electrónicos bancarios mediante Gmail API
- Extracción de datos de transacciones usando plantillas configurables con regex
- Publicación de eventos a broker MQTT para procesamiento automático
- Integración con Google OAuth para acceso seguro a Gmail
- Soporte para múltiples usuarios y configuraciones personalizadas

### MQTT Event Listener
- Integración con broker MQTT (ej: Mosquitto)
- Suscripción al tópico `colli_finance/email_listener`
- Procesamiento automático de transacciones desde eventos MQTT
- Registro de auditoría con origen MQTT
- Validación de payload con esquemas Pydantic

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y de alto rendimiento
- **Python 3.11+**: Lenguaje de programación
- **SQLAlchemy 2.0**: ORM asíncrono para manejo de base de datos
- **Alembic**: Gestión de migraciones de base de datos
- **Pydantic**: Validación de datos y configuración

### Base de Datos
- **PostgreSQL 13+**: Base de datos relacional
- **asyncpg**: Driver asíncrono de PostgreSQL
- **psycopg2**: Driver síncrono para migraciones

### Seguridad
- **python-jose**: Gestión de tokens JWT
- **passlib + bcrypt**: Hashing seguro de contraseñas
- **OAuth2**: Esquema de autenticación

### Email Listener
- **google-auth**: Autenticación con Google OAuth
- **google-api-python-client**: Cliente de Gmail API
- **paho-mqtt**: Cliente MQTT para publicación de eventos

### Logging y Monitoreo
- **python-json-logger**: Logs estructurados en JSON
- **Loki**: Agregación y consulta de logs (opcional)

### Desarrollo y Testing
- **pytest**: Framework de testing
- **pytest-asyncio**: Soporte para tests asíncronos
- **Docker**: Containerización
- **Docker Compose**: Orquestación de servicios

## 📦 Requisitos

- Python 3.11 o superior
- PostgreSQL 13 o superior
- Docker y Docker Compose (opcional, para deployment)

## 🚀 Instalación

### Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/rafavg77/colli_finance.git
   cd colli_finance
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar dependencias de desarrollo** (opcional):
   ```bash
   pip install -r requirements-dev.txt
   ```

## ⚙️ Configuración

1. **Copiar el archivo de ejemplo de variables de entorno**:
   ```bash
   cp .env.example .env
   ```

2. **Configurar variables de entorno en `.env`**:

### Variables de Aplicación
```bash
APP_NAME=Colli Finance API
SERVICE_NAME=colli-finance
ENVIRONMENT=local  # local, dev, prod
LOG_LEVEL=INFO     # DEBUG, INFO, WARNING, ERROR
```

### Variables de Base de Datos
```bash
DATABASE_USE=dev   # dev, prod, test
DATABASE_ECHO=false
MIGRATE_ON_START=true
RESET_DB_ON_START=false  # ¡CUIDADO! Elimina todos los datos

# URLs de conexión (usar asyncpg para SQLAlchemy)
# Para Docker, usar 'db' como host. Para local, usar 'localhost'

```

### Variables de Autenticación
```bash
SECRET_KEY=tu-clave-secreta-muy-segura-aqui  # ¡Cambiar en producción!
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Variables de Bancos
```bash
# Formato: Nombre:code:display_name;...
BANKS_LIST=Banregio:banregio:Banregio;Banorte:banorte:Banorte;Santander:santander:Santander;HeyBanco:heybanco:HeyBanco
```

### Variables de Logging (opcional)
```bash
LOKI_URL=http://localhost:3100/loki/api/v1/push
```

### Variables de MQTT Event Listener
```bash
MQTT_BROKER_HOST=localhost     # Host del broker MQTT (ej: mosquitto)
MQTT_BROKER_PORT=1883          # Puerto del broker MQTT
MQTT_USERNAME=                  # Usuario para autenticación MQTT (opcional)
MQTT_PASSWORD=                  # Contraseña para autenticación MQTT (opcional)
MQTT_TOPIC=colli_finance/email_listener  # Tópico MQTT a suscribirse
```

### Variables de Email Listener Service
```bash
EMAIL_LISTENER_ENABLED=false    # Habilitar/deshabilitar el servicio de email listener
EMAIL_LISTENER_POLL_INTERVAL=60 # Intervalo en segundos para revisar correos
EMAIL_LISTENER_MAX_RESULTS=10   # Máximo de correos a procesar por verificación
```

> **Nota**: Para configurar el Email Listener, se requiere configurar las credenciales de Google OAuth a través de los endpoints de `/listener/credentials`. Ver [documentación completa](docs/EMAIL_LISTENER.md).

### Variables de Carga de Archivos
```bash
UPLOAD_DIR=uploads
UPLOAD_MAX_MB=5
UPLOAD_ALLOWED_CONTENT_TYPES=application/pdf
UPLOAD_BLOCKED_CONTENT_TYPES=image/svg+xml
UPLOAD_ALLOWED_EXTS=.png,.jpg,.jpeg,.gif,.webp,.bmp,.tif,.tiff,.pdf
UPLOAD_BLOCKED_EXTS=.svg,.svgz
```

## ▶️ Ejecución

### Desarrollo Local

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`

### Documentación Interactiva

Una vez iniciada la aplicación, puedes acceder a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Proceso de Inicio

Al arrancar, la aplicación ejecuta automáticamente:

1. **Creación de base de datos**: Si no existe, se crea automáticamente
2. **Migraciones**: Si `MIGRATE_ON_START=true`, ejecuta migraciones pendientes de Alembic
3. **Reset de esquema** (opcional): Si `RESET_DB_ON_START=true`, elimina y recrea todas las tablas (⚠️ **solo en desarrollo**)
4. **Seed de categorías**: Inserta categorías predeterminadas (`Despensa`, `Salud`, `Diversión`, `Alimenos`, `Educación`, `Transporte`, `Servios`)

> **Nota**: Algunas categorías predeterminadas tienen errores tipográficos en el código fuente ("Alimenos" en lugar de "Alimentos" y "Servios" en lugar de "Servicios").

## 🗄️ Base de Datos

### Modelos Principales

- **User**: Usuarios del sistema
- **Bank**: Catálogo de bancos
- **Card**: Tarjetas bancarias (débito/crédito)
- **Category**: Categorías de transacciones
- **Transaction**: Transacciones (ingresos/gastos)
- **Attachment**: Archivos adjuntos
- **Audit**: Registro de auditoría
- **Listener**: Configuración para listeners/webhooks

### Migraciones

#### Crear una nueva migración:
```bash
make migrate
# o manualmente:
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

#### Ejecutar migraciones:
```bash
make migrate
```

#### Ver historial de migraciones:
```bash
alembic history
```

#### Revertir migración:
```bash
alembic downgrade -1  # Retrocede una versión
```

## 🔌 API Endpoints

### Sistema
- `GET /health` - Verificación de estado de la API

### Autenticación
- `POST /auth/register` - Registro de nuevos usuarios
- `POST /auth/login` - Login con email y contraseña
- `POST /auth/login-phone` - Login con teléfono y contraseña

### Usuarios
- `GET /users` - Listar usuarios (admin)
- `GET /users/me` - Obtener perfil del usuario autenticado
- `POST /users` - Crear usuario
- `PATCH /users/{user_id}` - Actualizar usuario
- `DELETE /users/{user_id}` - Eliminar usuario

### Categorías
- `GET /categories` - Listar todas las categorías
- `GET /categories/{category_id}` - Obtener categoría por ID
- `POST /categories` - Crear nueva categoría
- `PATCH /categories/{category_id}` - Actualizar categoría
- `DELETE /categories/{category_id}` - Eliminar categoría

### Tarjetas
- `GET /cards` - Listar tarjetas del usuario
- `GET /cards/{card_id}` - Obtener tarjeta por ID
- `POST /cards` - Crear nueva tarjeta
- `PATCH /cards/{card_id}` - Actualizar tarjeta
- `DELETE /cards/{card_id}` - Eliminar tarjeta

### Transacciones
- `GET /transactions` - Listar transacciones del usuario
- `GET /transactions/{transaction_id}` - Obtener transacción por ID
- `POST /transactions` - Crear nueva transacción
- `PATCH /transactions/{transaction_id}` - Actualizar transacción
- `DELETE /transactions/{transaction_id}` - Eliminar transacción

### Transferencias
- `POST /transfers` - Crear transferencia entre tarjetas propias
- `GET /transfers/{source_tx_id}/{destination_tx_id}` - Obtener detalles de transferencia

### Carga de Archivos
- `POST /uploads/transactions` - Crear transacción con archivo adjunto
- `POST /uploads/transfers` - Crear transferencia con archivo adjunto

### Resúmenes
- `GET /summary/cards` - Obtener resumen de saldos por tarjeta (requiere parámetros `start_date` y `end_date`)

### Auditoría
- `GET /audit` - Consultar registros de auditoría del usuario

### Email Listener (Nuevo)
- `GET /listener/credentials` - Obtener credenciales de listener del usuario
- `POST /listener/credentials` - Crear credenciales de listener
- `PATCH /listener/credentials` - Actualizar credenciales de listener
- `DELETE /listener/credentials` - Eliminar credenciales de listener
- `GET /listener/templates` - Listar plantillas de email
- `POST /listener/templates` - Crear plantilla de email
- `GET /listener/templates/{template_id}` - Obtener plantilla por ID
- `PATCH /listener/templates/{template_id}` - Actualizar plantilla
- `DELETE /listener/templates/{template_id}` - Eliminar plantilla
- `GET /listener/configs` - Listar configuraciones de listener
- `POST /listener/configs` - Crear configuración de listener
- `GET /listener/configs/{config_id}` - Obtener configuración por ID
- `PATCH /listener/configs/{config_id}` - Actualizar configuración
- `DELETE /listener/configs/{config_id}` - Eliminar configuración

### Hábitos (Deprecado)
- `POST /habitos/registrar` - Registrar hábito (pendiente de eliminación)

## 🔌 Email Listener Service

La API incluye un servicio de Email Listener que monitorea la bandeja de entrada de Gmail del usuario para detectar correos de transacciones bancarias y publicarlos automáticamente como eventos MQTT.

### Arquitectura

```
Gmail Inbox → Email Listener Service → MQTT Broker → MQTT Listener Service → Transaction Database
```

### Características

- **Monitoreo Automático**: Revisa la bandeja de entrada de Gmail periódicamente
- **Google OAuth**: Autenticación segura usando credenciales de Google
- **Plantillas Configurables**: Extracción de datos mediante expresiones regulares
- **Publicación MQTT**: Envío de eventos al broker MQTT para procesamiento
- **Multi-usuario**: Soporte para múltiples usuarios con configuraciones independientes
- **Logs Estructurados**: Registro detallado de todas las operaciones

### Configuración

1. **Habilitar el servicio** en `.env`:
   ```bash
   EMAIL_LISTENER_ENABLED=true
   EMAIL_LISTENER_POLL_INTERVAL=60  # Revisar cada 60 segundos
   EMAIL_LISTENER_MAX_RESULTS=10    # Máximo 10 correos por verificación
   ```

2. **Configurar credenciales de Google OAuth** mediante los endpoints de `/listener/credentials`

3. **Crear plantillas de email** para cada banco usando expresiones regulares para extracción de datos

4. **Vincular plantillas con tarjetas** mediante configuraciones de listener

### Formato del Evento Publicado

El Email Listener publica eventos al topic MQTT con el siguiente formato:

```json
{
  "id_usuario": 1,
  "correo_usuario": "user@example.com",
  "tarjetas": [
    {
      "id_tarjeta": 1,
      "transaction": [
        {
          "amount": "100.00",
          "description": "Compra en tienda",
          "income": "",
          "expense": "100.00",
          "type": "expense",
          "operation_date": "2025-10-19"
        }
      ]
    }
  ]
}
```

### Documentación Completa

Para información detallada sobre configuración, plantillas, patrones de extracción y troubleshooting, consulta la [documentación completa del Email Listener](docs/EMAIL_LISTENER.md).

### Deshabilitar el Servicio

Para deshabilitar temporalmente:

```bash
DISABLE_EMAIL_LISTENER=1 uvicorn app.main:app --reload
```

O en `.env`:

```bash
EMAIL_LISTENER_ENABLED=false
```

## 🔌 MQTT Event Listener

La API incluye un listener de eventos MQTT que se conecta automáticamente a un broker MQTT (como Mosquitto) y procesa transacciones recibidas desde eventos externos.

### Configuración

El listener MQTT se configura mediante variables de entorno en el archivo `.env`:

```bash
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=tu_usuario
MQTT_PASSWORD=tu_contraseña
MQTT_TOPIC=colli_finance/email_listener
```

### Formato del Mensaje

El listener espera mensajes en el tópico configurado con el siguiente formato JSON:

```json
{
  "id_usuario": 1,
  "correo_usuario": "tu_email@gmail.com",
  "tarjetas": [
    {
      "id_tarjeta": 1,
      "transaction": [
        {
          "amount": "100.00",
          "description": "Pago recibido",
          "income": "100.00",
          "expense": "",
          "type": "income",
          "operation_date": "2025-10-19"
        }
      ]
    }
  ]
}
```

### Campos del Mensaje

- **id_usuario**: ID del usuario en la base de datos
- **correo_usuario**: Email del usuario
- **tarjetas**: Array de tarjetas con sus transacciones
  - **id_tarjeta**: ID de la tarjeta en la base de datos
  - **transaction**: Array de transacciones
    - **amount**: Monto de la transacción (opcional)
    - **description**: Descripción de la transacción
    - **income**: Monto de ingreso (usar "" para 0)
    - **expense**: Monto de egreso (usar "" para 0)
    - **type**: Tipo de transacción ("income" o "expense")
    - **operation_date**: Fecha de la operación (formato: YYYY-MM-DD)

### Procesamiento de Eventos

Cuando el listener recibe un mensaje:

1. **Validación**: Valida el payload contra el esquema Pydantic
2. **Verificación**: Verifica que la tarjeta existe y pertenece al usuario
3. **Creación**: Crea la transacción en la base de datos
4. **Auditoría**: Registra en la tabla de auditoría con `source: "mqtt_event"`
5. **Logging**: Emite logs estructurados de todo el proceso

### Auditoría MQTT

Todas las transacciones creadas desde eventos MQTT incluyen un registro de auditoría especial:

```json
{
  "action": "create",
  "resource": "transaction",
  "details": {
    "transaction_id": 123,
    "source": "mqtt_event",
    "mqtt_topic": "colli_finance/email_listener",
    "email": "usuario@example.com",
    "card_id": 1,
    "type": "income"
  }
}
```

### Ciclo de Vida

El listener MQTT:
- **Inicia** automáticamente al arrancar la aplicación
- **Reconecta** automáticamente si se pierde la conexión
- **Detiene** correctamente al apagar la aplicación

Para deshabilitar el listener durante el desarrollo o testing:

```bash
DISABLE_MQTT_LISTENER=1 uvicorn app.main:app --reload
```

### Ejemplo con Mosquitto

Para probar el listener con Mosquitto:

```bash
# Instalar Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# Publicar mensaje de prueba
mosquitto_pub -h localhost -p 1883 -t "colli_finance/email_listener" -m '{
  "id_usuario": 1,
  "correo_usuario": "test@example.com",
  "tarjetas": [{
    "id_tarjeta": 1,
    "transaction": [{
      "description": "Test transaction",
      "income": "100.00",
      "expense": "",
      "type": "income",
      "operation_date": "2025-10-19"
    }]
  }]
}'
```

## 🔐 Autenticación y Seguridad

### JWT (JSON Web Tokens)

La API utiliza autenticación basada en JWT:

1. **Registro/Login**: Obtén un token de acceso
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "usuario@example.com", "password": "contraseña"}'
   ```

2. **Uso del token**: Incluye el token en el header de autorización
   ```bash
   curl -X GET "http://localhost:8000/users/me" \
     -H "Authorization: Bearer tu-token-jwt-aqui"
   ```

### Hashing de Contraseñas

- Las contraseñas se almacenan usando bcrypt con salt automático
- Nunca se almacenan contraseñas en texto plano
- El factor de trabajo de bcrypt garantiza protección contra ataques de fuerza bruta

### Middleware de Seguridad

- **CORS**: Configurado para permitir orígenes específicos
- **Request Logging**: Todas las peticiones se registran con detalles
- **Error Handling**: Manejo centralizado de excepciones

## 📎 Adjuntos y Carga de Archivos

La API soporta la carga de archivos (comprobantes, recibos, facturas) asociados a transacciones y transferencias.

### Endpoints de Carga

#### Transacción con Archivo
```bash
POST /uploads/transactions
Content-Type: multipart/form-data

Campos:
- file: archivo (requerido)
- description: string (requerido)
- card_id: integer (requerido)
- category_id: integer (opcional)
- income: decimal (opcional, default: 0)
- expenses: decimal (opcional, default: 0)
- executed: boolean (opcional, default: true)
- operation_date: string ISO (requerido)
```

#### Transferencia con Archivo
```bash
POST /uploads/transfers
Content-Type: multipart/form-data

Campos:
- file: archivo (requerido)
- source_card_id: integer (requerido)
- destination_card_id: integer (requerido)
- amount: decimal (requerido)
- description: string (opcional)
- category_id: integer (opcional)
- operation_date: string ISO (requerido)
```

### Configuración de Archivos

Variables de entorno para control de cargas:

- **UPLOAD_DIR**: Directorio de almacenamiento (default: `uploads`)
- **UPLOAD_MAX_MB**: Tamaño máximo en MB (default: `5`)
- **UPLOAD_ALLOWED_CONTENT_TYPES**: Content-types adicionales permitidos
- **UPLOAD_BLOCKED_CONTENT_TYPES**: Content-types bloqueados (default: `image/svg+xml`)
- **UPLOAD_ALLOWED_EXTS**: Extensiones permitidas (default: `.png,.jpg,.jpeg,.gif,.webp,.bmp,.tif,.tiff,.pdf`)
- **UPLOAD_BLOCKED_EXTS**: Extensiones bloqueadas (default: `.svg,.svgz`)

### Validaciones

- Validación de tamaño de archivo
- Validación de tipo MIME
- Validación de extensión de archivo
- Protección contra archivos maliciosos (SVG bloqueados por default)

## 📊 Logging y Monitoreo

### Logs Estructurados

Todos los logs se emiten en formato JSON estructurado con campos consistentes:

```json
{
  "timestamp": "2024-10-19T20:00:00.000Z",
  "level": "INFO",
  "service": "colli-finance",
  "event": "request_completed",
  "status_code": 200,
  "duration_ms": 45,
  "method": "GET",
  "path": "/users/me"
}
```

### Integración con Loki

Si configuras `LOKI_URL`, los logs se enviarán automáticamente a Grafana Loki para:
- Agregación centralizada de logs
- Búsqueda y filtrado avanzado
- Creación de dashboards
- Alertas basadas en logs

### Niveles de Log

- **DEBUG**: Información detallada de desarrollo
- **INFO**: Eventos normales de la aplicación
- **WARNING**: Situaciones anómalas pero no críticas
- **ERROR**: Errores que requieren atención

### Eventos Registrados

- Inicio y fin de peticiones HTTP
- Operaciones de base de datos
- Autenticación de usuarios
- Creación, actualización y eliminación de recursos
- Errores y excepciones

## 🐳 Docker

### Docker Compose Local

Construir y ejecutar con imagen local:

```bash
# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus valores
nano .env

# Construir y levantar servicios
docker compose -f docker-compose.local.yml up --build

# En modo detached (background)
docker compose -f docker-compose.local.yml up -d --build
```

La API estará disponible en `http://localhost:8000` y PostgreSQL en `localhost:5433`.

### Docker Compose con Imagen de Docker Hub

Si tienes una imagen publicada:

```bash
docker compose -f docker-compose.dockerhub.yml up
```

Asegúrate de actualizar la referencia de imagen en el archivo.

### Servicios Incluidos

- **api**: API de FastAPI
- **db**: PostgreSQL 15
- **uploads-init**: Inicializador de permisos para directorio de uploads
- **loki** (opcional): Agregador de logs

### Volúmenes

- `postgres_data`: Datos persistentes de PostgreSQL
- `uploads_data`: Archivos subidos

### Comandos Útiles

```bash
# Ver logs
docker compose logs -f api

# Ejecutar comando en contenedor
docker compose exec api bash

# Detener servicios
docker compose down

# Eliminar volúmenes (¡borra datos!)
docker compose down -v
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Instalar dependencias de desarrollo
make install-dev

# Ejecutar todos los tests
make test

# O con pytest directamente
pytest

# Tests específicos
pytest tests/test_auth.py
pytest tests/test_transfers.py -v

# Con cobertura
pytest --cov=app --cov-report=html
```

### Tests en Docker

```bash
make test-docker
```

Esto ejecuta los tests dentro del contenedor Docker con la configuración de CI.

### Tests Disponibles

- `test_health.py`: Verificación del endpoint de health
- `test_auth.py`: Tests de autenticación y registro
- `test_transfers.py`: Tests de transferencias entre tarjetas
- `conftest.py`: Fixtures compartidos para tests

### Estructura de Tests

```python
@pytest.mark.asyncio
async def test_ejemplo(client, test_user):
    response = await client.get("/endpoint")
    assert response.status_code == 200
```

## 👨‍💻 Desarrollo

### Estructura del Proyecto

```
colli_finance/
├── app/
│   ├── core/           # Configuración, seguridad, dependencias
│   ├── crud/           # Operaciones de base de datos
│   ├── db/             # Modelos y sesión de BD
│   ├── routers/        # Endpoints de la API
│   ├── schemas/        # Esquemas Pydantic
│   ├── services/       # Lógica de negocio
│   ├── tools/          # Utilidades y scripts
│   └── main.py         # Punto de entrada de la aplicación
├── alembic/            # Migraciones de base de datos
├── tests/              # Tests automatizados
├── uploads/            # Archivos subidos (generado)
├── .env.example        # Ejemplo de variables de entorno
├── .gitignore          # Archivos ignorados por git
├── Dockerfile          # Imagen Docker
├── docker-compose.*.yml # Configuraciones Docker Compose
├── Makefile            # Comandos útiles
├── requirements.txt    # Dependencias de producción
└── requirements-dev.txt # Dependencias de desarrollo
```

### Makefile

El proyecto incluye un Makefile con comandos útiles:

```bash
make install-dev    # Instalar dependencias de desarrollo
make migrate        # Ejecutar migraciones
make test          # Ejecutar tests
make test-docker   # Ejecutar tests en Docker
```

### Convenciones de Código

- **PEP 8**: Estilo de código Python
- **Type Hints**: Uso de anotaciones de tipos
- **Async/Await**: Programación asíncrona
- **Pydantic Models**: Validación de datos
- **SQLAlchemy 2.0**: ORM moderno con sintaxis async

### Workflow de Desarrollo

1. Crear rama feature: `git checkout -b feature/nombre-feature`
2. Realizar cambios
3. Ejecutar tests: `make test`
4. Commit: `git commit -m "descripción"`
5. Push: `git push origin feature/nombre-feature`
6. Crear Pull Request

## 📝 TODO y Roadmap

Ver [TODO.md](TODO.md) para:
- Características completadas
- Funcionalidades pendientes
- Mejoras planificadas

## 📄 Licencia

Este proyecto está bajo licencia privada. Todos los derechos reservados.

## 👤 Autor

([@rafavg77](https://github.com/rafavg77))

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request
