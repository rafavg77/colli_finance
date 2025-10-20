# Email Listener Service

El servicio Email Listener monitorea la bandeja de entrada de Gmail del usuario para detectar correos de transacciones bancarias y publicar eventos en el broker MQTT.

## Arquitectura

```
Gmail Inbox → Email Listener Service → MQTT Broker → MQTT Listener Service → Transaction Database
```

### Componentes

1. **Email Listener Service** (`app/services/email_listener.py`)
   - Monitorea correos de Gmail usando Google Gmail API
   - Extrae información de transacciones usando plantillas (templates)
   - Publica eventos al topic MQTT `colli_finance/email_listener`

2. **MQTT Listener Service** (`app/services/mqtt_listener.py`)
   - Escucha eventos del topic MQTT
   - Crea transacciones en la base de datos
   - Registra auditoría de eventos

## Configuración

### Variables de Entorno

Agregar en tu archivo `.env`:

```env
# Email Listener Configuration
EMAIL_LISTENER_ENABLED=true
EMAIL_LISTENER_POLL_INTERVAL=60
EMAIL_LISTENER_MAX_RESULTS=10

# MQTT Configuration (requerido)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=colli_finance/email_listener
```

### Descripción de Variables

- `EMAIL_LISTENER_ENABLED`: Habilita/deshabilita el servicio (default: false)
- `EMAIL_LISTENER_POLL_INTERVAL`: Intervalo en segundos para revisar correos (default: 60)
- `EMAIL_LISTENER_MAX_RESULTS`: Máximo de correos a procesar por verificación (default: 10)
- `MQTT_BROKER_HOST`: Host del broker MQTT (requerido)
- `MQTT_BROKER_PORT`: Puerto del broker MQTT (default: 1883)
- `MQTT_TOPIC`: Topic MQTT para publicar eventos (default: colli_finance/email_listener)

## Configuración de Usuario

Para que el Email Listener funcione, cada usuario debe:

### 1. Configurar Credenciales de Google OAuth

Crear credenciales en `/listener/credentials`:

```json
{
  "status": "enabled",
  "google_credentials": {
    "client_id": "xxx.apps.googleusercontent.com",
    "client_secret": "xxx",
    "redirect_uris": ["http://localhost:8080/"]
  },
  "google_access_token": {
    "token": "ya29.xxx",
    "refresh_token": "1//xxx",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "xxx.apps.googleusercontent.com",
    "client_secret": "xxx",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
  }
}
```

### 2. Configurar Plantillas de Email

Crear plantillas en `/listener/templates` para cada banco:

```json
{
  "bank_id": 1,
  "template_code": "BANREGIO_EXPENSE",
  "email_sender": "alertas@banregio.com",
  "subject_pattern": "Compra.*tarjeta",
  "amount_pattern": "\\$([0-9,\\.]+)",
  "description_pattern": "en (.+?)\\.",
  "date_pattern": null,
  "transaction_type": "expense",
  "is_active": true
}
```

### 3. Configurar Listener Configs

Vincular plantillas con tarjetas en `/listener/configs`:

```json
{
  "listener_cred_id": 1,
  "listener_template_id": 1,
  "card_id": 1,
  "is_active": true
}
```

## Formato de Evento MQTT

El Email Listener publica eventos en el siguiente formato JSON:

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

## Patrones de Extracción

Las plantillas usan expresiones regulares (regex) para extraer información:

### Ejemplos de Patrones

**amount_pattern**: Extrae el monto
```regex
\$([0-9,\.]+)
```
Ejemplo: "Compra por $100.50" → "100.50"

**description_pattern**: Extrae la descripción
```regex
en (.+?)\.
```
Ejemplo: "Compra en OXXO." → "OXXO"

**subject_pattern**: Valida el asunto del correo
```regex
Compra.*tarjeta
```
Valida que el asunto contenga "Compra" y "tarjeta"

## Flujo de Procesamiento

1. **Verificación de Correos**: Cada 60 segundos (configurable)
2. **Filtrado**: Solo correos de la última hora
3. **Validación de Remitente**: Verifica que el correo venga del banco configurado
4. **Validación de Asunto**: Aplica pattern del subject si está configurado
5. **Extracción de Datos**: Usa patterns para extraer amount, description, date
6. **Validación**: Si no se puede extraer el amount, se descarta el correo
7. **Publicación MQTT**: Envía el evento al broker
8. **Procesamiento**: MQTT Listener recibe y crea la transacción

## Logging

El servicio genera logs estructurados para cada operación:

```json
{
  "event": "transaction_published",
  "extra": {
    "user_id": 1,
    "card_id": 1,
    "type": "expense",
    "amount": "100.50"
  }
}
```

### Eventos Importantes

- `email_listener_start`: Servicio iniciado
- `emails_fetched`: Correos obtenidos de Gmail
- `template_matched`: Correo coincide con plantilla
- `transaction_published`: Evento publicado a MQTT
- `email_listener_error`: Error en el servicio

## Testing

### Ejecutar Tests Unitarios

```bash
pytest tests/test_email_listener.py -v
```

### Ejemplo Manual

```bash
# Configurar variables de entorno
export EMAIL_LISTENER_ENABLED=true
export MQTT_BROKER_HOST=localhost

# Ejecutar ejemplo
python examples/email_listener_example.py
```

## Seguridad

### Tokens de Acceso

- Los tokens de Google OAuth se almacenan en la base de datos
- Los tokens expirados se refrescan automáticamente
- Los tokens requieren el scope `gmail.readonly`

### Privacidad

- Solo se leen correos (readonly)
- Solo se procesan correos de remitentes configurados
- Los correos no se almacenan, solo se extraen datos de transacciones

## Troubleshooting

### El servicio no inicia

1. Verificar `EMAIL_LISTENER_ENABLED=true` en .env
2. Verificar que MQTT broker esté configurado
3. Revisar logs de inicio

### No detecta correos

1. Verificar credenciales de Google OAuth
2. Verificar que el token no esté expirado
3. Verificar que existan configuraciones activas
4. Revisar que el email_sender coincida

### Los correos no generan transacciones

1. Verificar que los patterns de la plantilla sean correctos
2. Probar patterns en https://regex101.com/
3. Verificar logs para ver si el correo fue procesado
4. Verificar que la tarjeta exista y pertenezca al usuario

## Desactivar el Servicio

Para desactivar temporalmente:

```bash
export DISABLE_EMAIL_LISTENER=1
```

O en producción, establecer en .env:

```env
EMAIL_LISTENER_ENABLED=false
```

## Dependencias

El servicio requiere las siguientes librerías de Python:

```
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0
paho-mqtt==1.6.1
```

Estas se instalan automáticamente con:

```bash
pip install -r requirements.txt
```
