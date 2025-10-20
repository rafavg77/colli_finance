import os
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import date

import pytest
import paho.mqtt.client as mqtt

from app.schemas.mqtt_event import MqttEmailEvent, MqttCardData, MqttTransactionData


# Unit tests for schema validation (no database required)

def test_mqtt_transaction_schema_income():
    """Test MQTT transaction schema validation for income"""
    transaction_data = {
        "amount": "100.00",
        "description": "Payment received",
        "income": "100.00",
        "expense": "",
        "type": "income",
        "operation_date": "2025-10-19"
    }
    
    transaction = MqttTransactionData(**transaction_data)
    
    assert transaction.description == "Payment received"
    assert transaction.income == "100.00"
    assert transaction.expense == "0.00"  # Empty string converted to 0.00
    assert transaction.type == "income"
    assert transaction.operation_date == date(2025, 10, 19)


def test_mqtt_transaction_schema_expense():
    """Test MQTT transaction schema validation for expense"""
    transaction_data = {
        "amount": "50.00",
        "description": "Store purchase",
        "income": "",
        "expense": "50.00",
        "type": "expense",
        "operation_date": "2025-10-19"
    }
    
    transaction = MqttTransactionData(**transaction_data)
    
    assert transaction.description == "Store purchase"
    assert transaction.income == "0.00"  # Empty string converted to 0.00
    assert transaction.expense == "50.00"
    assert transaction.type == "expense"


def test_mqtt_email_event_schema():
    """Test MQTT email event full schema validation"""
    event_data = {
        "id_usuario": 1,
        "correo_usuario": "user@example.com",
        "tarjetas": [
            {
                "id_tarjeta": 1,
                "transaction": [
                    {
                        "amount": "100.00",
                        "description": "Test transaction",
                        "income": "100.00",
                        "expense": "",
                        "type": "income",
                        "operation_date": "2025-10-19"
                    }
                ]
            }
        ]
    }
    
    event = MqttEmailEvent(**event_data)
    
    assert event.id_usuario == 1
    assert event.correo_usuario == "user@example.com"
    assert len(event.tarjetas) == 1
    assert event.tarjetas[0].id_tarjeta == 1
    assert len(event.tarjetas[0].transaction) == 1


def test_mqtt_message_parsing():
    """Test MQTT message parsing and validation"""
    # Valid message payload
    payload = json.dumps({
        "id_usuario": 1,
        "correo_usuario": "test@example.com",
        "tarjetas": [
            {
                "id_tarjeta": 1,
                "transaction": [
                    {
                        "amount": "100.00",
                        "description": "Test",
                        "income": "100.00",
                        "expense": "",
                        "type": "income",
                        "operation_date": "2025-10-19"
                    }
                ]
            }
        ]
    })
    
    # Parse and validate
    data = json.loads(payload)
    event = MqttEmailEvent(**data)
    
    assert event.id_usuario == 1
    assert event.correo_usuario == "test@example.com"


def test_mqtt_transaction_schema_empty_amounts():
    """Test that empty string amounts are converted to 0.00"""
    transaction_data = {
        "description": "Test",
        "income": "",
        "expense": "",
        "type": "income",
        "operation_date": "2025-10-19"
    }
    
    transaction = MqttTransactionData(**transaction_data)
    
    assert transaction.income == "0.00"
    assert transaction.expense == "0.00"


def test_mqtt_transaction_schema_invalid_type():
    """Test that invalid transaction type is rejected"""
    transaction_data = {
        "description": "Test",
        "income": "100.00",
        "expense": "",
        "type": "invalid_type",
        "operation_date": "2025-10-19"
    }
    
    with pytest.raises(Exception):  # Pydantic validation error
        MqttTransactionData(**transaction_data)


def test_mqtt_email_event_multiple_cards():
    """Test MQTT email event with multiple cards"""
    event_data = {
        "id_usuario": 1,
        "correo_usuario": "user@example.com",
        "tarjetas": [
            {
                "id_tarjeta": 1,
                "transaction": [
                    {
                        "description": "Transaction 1",
                        "income": "100.00",
                        "expense": "",
                        "type": "income",
                        "operation_date": "2025-10-19"
                    }
                ]
            },
            {
                "id_tarjeta": 2,
                "transaction": [
                    {
                        "description": "Transaction 2",
                        "income": "",
                        "expense": "50.00",
                        "type": "expense",
                        "operation_date": "2025-10-19"
                    }
                ]
            }
        ]
    }
    
    event = MqttEmailEvent(**event_data)
    
    assert event.id_usuario == 1
    assert len(event.tarjetas) == 2
    assert event.tarjetas[0].id_tarjeta == 1
    assert event.tarjetas[1].id_tarjeta == 2

