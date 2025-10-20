# Colli Finance Examples

This directory contains example scripts and utilities for working with the Colli Finance API.

## MQTT Publisher Example

The `mqtt_publisher_example.py` script demonstrates how to send transaction events to the Colli Finance MQTT listener.

### Prerequisites

1. Install required dependencies:
   ```bash
   pip install paho-mqtt
   ```

2. Ensure you have a running MQTT broker (e.g., Mosquitto):
   ```bash
   # Install Mosquitto on Ubuntu/Debian
   sudo apt-get install mosquitto
   
   # Start Mosquitto
   sudo systemctl start mosquitto
   ```

3. Ensure Colli Finance API is running with MQTT listener enabled:
   ```bash
   # Configure .env file with MQTT settings
   MQTT_BROKER_HOST=localhost
   MQTT_BROKER_PORT=1883
   MQTT_TOPIC=colli_finance/email_listener
   
   # Start the API
   uvicorn app.main:app --reload
   ```

### Usage

Basic usage with default values:

```bash
python examples/mqtt_publisher_example.py
```

With custom parameters:

```bash
python examples/mqtt_publisher_example.py \
  --host localhost \
  --port 1883 \
  --user-id 1 \
  --card-id 1 \
  --email "user@example.com"
```

### Command Line Arguments

- `--host`: MQTT broker hostname (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--topic`: MQTT topic to publish to (default: colli_finance/email_listener)
- `--user-id`: User ID from the database (default: 1)
- `--card-id`: Card ID from the database (default: 1)
- `--email`: User email address (default: test@example.com)

### Example Output

```
Connecting to MQTT broker at localhost:1883...

Publishing to topic: colli_finance/email_listener
Payload:
{
  "id_usuario": 1,
  "correo_usuario": "test@example.com",
  "tarjetas": [
    {
      "id_tarjeta": 1,
      "transaction": [
        {
          "amount": "100.00",
          "description": "Test income transaction from MQTT",
          "income": "100.00",
          "expense": "",
          "type": "income",
          "operation_date": "2025-10-19"
        },
        {
          "amount": "50.00",
          "description": "Test expense transaction from MQTT",
          "income": "",
          "expense": "50.00",
          "type": "expense",
          "operation_date": "2025-10-19"
        }
      ]
    }
  ]
}

✓ Message published successfully!

Disconnected from broker.
```

### Verification

After publishing an event, you can verify the transactions were created by:

1. Checking the API logs for MQTT event processing messages
2. Querying the transactions endpoint:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/transactions
   ```
3. Checking the audit log for entries with `source: "mqtt_event"`:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/audit
   ```

### Troubleshooting

- **Connection refused**: Ensure Mosquitto is running and accessible
- **Transactions not created**: Check that the user_id and card_id exist in the database
- **Invalid payload**: Verify the JSON structure matches the expected schema
