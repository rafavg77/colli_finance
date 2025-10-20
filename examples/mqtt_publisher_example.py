#!/usr/bin/env python3
"""
Example MQTT Client to send test events to Colli Finance API

This script demonstrates how to send transaction events to the Colli Finance
MQTT listener. It can be used for testing the MQTT integration.

Usage:
    python examples/mqtt_publisher_example.py

Requirements:
    pip install paho-mqtt
"""

import json
import paho.mqtt.client as mqtt
from datetime import date


def create_sample_event(user_id: int, card_id: int, email: str):
    """Create a sample MQTT event payload"""
    return {
        "id_usuario": user_id,
        "correo_usuario": email,
        "tarjetas": [
            {
                "id_tarjeta": card_id,
                "transaction": [
                    {
                        "amount": "100.00",
                        "description": "Test income transaction from MQTT",
                        "income": "100.00",
                        "expense": "",
                        "type": "income",
                        "operation_date": date.today().isoformat()
                    },
                    {
                        "amount": "50.00",
                        "description": "Test expense transaction from MQTT",
                        "income": "",
                        "expense": "50.00",
                        "type": "expense",
                        "operation_date": date.today().isoformat()
                    }
                ]
            }
        ]
    }


def publish_event(broker_host="localhost", broker_port=1883, topic="colli_finance/email_listener"):
    """Publish a test event to the MQTT broker"""
    
    # Create MQTT client
    client = mqtt.Client()
    
    # Connect to broker
    print(f"Connecting to MQTT broker at {broker_host}:{broker_port}...")
    client.connect(broker_host, broker_port, keepalive=60)
    
    # Create sample event
    # NOTE: Replace these values with actual user_id and card_id from your database
    event = create_sample_event(
        user_id=1,
        card_id=1,
        email="test@example.com"
    )
    
    # Convert to JSON
    payload = json.dumps(event, indent=2)
    
    print(f"\nPublishing to topic: {topic}")
    print(f"Payload:\n{payload}\n")
    
    # Publish message
    result = client.publish(topic, payload, qos=1)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✓ Message published successfully!")
    else:
        print(f"✗ Failed to publish message. Error code: {result.rc}")
    
    # Disconnect
    client.disconnect()
    print("\nDisconnected from broker.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Publish test MQTT events to Colli Finance")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="colli_finance/email_listener", help="MQTT topic")
    parser.add_argument("--user-id", type=int, default=1, help="User ID")
    parser.add_argument("--card-id", type=int, default=1, help="Card ID")
    parser.add_argument("--email", default="test@example.com", help="User email")
    
    args = parser.parse_args()
    
    try:
        publish_event(args.host, args.port, args.topic)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
