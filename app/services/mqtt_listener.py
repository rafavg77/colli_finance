import asyncio
import json
import threading
from typing import Any

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.crud.card import CardCRUD
from app.crud.transaction import TransactionCRUD
from app.db.session import AsyncSessionLocal
from app.schemas.mqtt_event import MqttEmailEvent
from app.services.audit import register_audit

logger = get_logger(__name__)
settings = get_settings()


class MqttListenerService:
    """Service to handle MQTT connection and message processing for email listener events"""
    
    def __init__(self):
        self.client: mqtt.Client | None = None
        self.running = False
        self.thread: threading.Thread | None = None
        
    def start(self):
        """Start MQTT listener in a separate thread"""
        if self.running:
            logger.warning("MQTT listener already running")
            return
            
        if not settings.mqtt_broker_host:
            logger.warning("MQTT broker host not configured, skipping MQTT listener startup")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_mqtt_client, daemon=True)
        self.thread.start()
        logger.info(
            "MQTT listener service started",
            extra={
                "details": {
                    "event": "mqtt_listener_start",
                    "extra": {
                        "broker": settings.mqtt_broker_host,
                        "port": settings.mqtt_broker_port,
                        "topic": settings.mqtt_topic,
                    }
                }
            }
        )
    
    def stop(self):
        """Stop MQTT listener"""
        if not self.running:
            return
            
        self.running = False
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("MQTT listener service stopped")
    
    def _run_mqtt_client(self):
        """Run MQTT client in a blocking loop"""
        try:
            self.client = mqtt.Client()
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            # Set credentials if provided
            if settings.mqtt_username and settings.mqtt_password:
                self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
            
            # Connect to broker
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=60)
            
            # Start loop
            self.client.loop_forever()
        except Exception as exc:
            logger.error(
                "Error in MQTT client loop",
                extra={
                    "details": {
                        "event": "mqtt_client_error",
                        "extra": {"error": str(exc), "error_type": type(exc).__name__}
                    }
                }
            )
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info(
                "Connected to MQTT broker",
                extra={
                    "details": {
                        "event": "mqtt_connected",
                        "extra": {"broker": settings.mqtt_broker_host}
                    }
                }
            )
            # Subscribe to topic
            client.subscribe(settings.mqtt_topic)
            logger.info(
                "Subscribed to MQTT topic",
                extra={
                    "details": {
                        "event": "mqtt_subscribed",
                        "extra": {"topic": settings.mqtt_topic}
                    }
                }
            )
        else:
            logger.error(
                "Failed to connect to MQTT broker",
                extra={
                    "details": {
                        "event": "mqtt_connection_failed",
                        "extra": {"return_code": rc}
                    }
                }
            )
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        if rc != 0:
            logger.warning(
                "Unexpected disconnection from MQTT broker",
                extra={
                    "details": {
                        "event": "mqtt_disconnected",
                        "extra": {"return_code": rc}
                    }
                }
            )
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received from MQTT broker"""
        try:
            logger.info(
                "MQTT message received",
                extra={
                    "details": {
                        "event": "mqtt_message_received",
                        "extra": {"topic": msg.topic}
                    }
                }
            )
            
            # Parse message payload
            payload_str = msg.payload.decode('utf-8')
            payload_data = json.loads(payload_str)
            
            # Validate payload against schema
            event = MqttEmailEvent(**payload_data)
            
            # Process the event asynchronously
            asyncio.run(self._process_mqtt_event(event))
            
        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON in MQTT message",
                extra={
                    "details": {
                        "event": "mqtt_message_invalid_json",
                        "extra": {"error": str(exc)}
                    }
                }
            )
        except ValidationError as exc:
            logger.error(
                "MQTT message validation failed",
                extra={
                    "details": {
                        "event": "mqtt_message_validation_error",
                        "extra": {"errors": exc.errors()}
                    }
                }
            )
        except Exception as exc:
            logger.error(
                "Error processing MQTT message",
                extra={
                    "details": {
                        "event": "mqtt_message_processing_error",
                        "extra": {"error": str(exc), "error_type": type(exc).__name__}
                    }
                }
            )
    
    async def _process_mqtt_event(self, event: MqttEmailEvent):
        """Process MQTT event and create transactions"""
        async with AsyncSessionLocal() as db:
            try:
                user_id = event.id_usuario
                
                logger.info(
                    "Processing MQTT event",
                    extra={
                        "details": {
                            "event": "mqtt_event_processing",
                            "extra": {
                                "user_id": user_id,
                                "email": event.correo_usuario,
                                "cards_count": len(event.tarjetas)
                            }
                        }
                    }
                )
                
                # Process each card's transactions
                for card_data in event.tarjetas:
                    card_id = card_data.id_tarjeta
                    
                    # Verify card exists and belongs to the user
                    card = await CardCRUD.get_by_id(db, card_id, user_id)
                    if not card:
                        logger.warning(
                            "Card not found or does not belong to user",
                            extra={
                                "details": {
                                    "event": "mqtt_card_not_found",
                                    "extra": {"card_id": card_id, "user_id": user_id}
                                }
                            }
                        )
                        continue
                    
                    # Process each transaction
                    for trans_data in card_data.transaction:
                        try:
                            # Determine income and expense amounts
                            income_amount = trans_data.income if trans_data.income else "0.00"
                            expense_amount = trans_data.expense if trans_data.expense else "0.00"
                            
                            # Create transaction
                            transaction = await TransactionCRUD.create(
                                db,
                                user_id=user_id,
                                card_id=card_id,
                                description=trans_data.description,
                                income=income_amount,
                                expenses=expense_amount,
                                executed=True,
                                operation_date=trans_data.operation_date,
                            )
                            
                            # Register audit trail indicating MQTT source
                            await register_audit(
                                db,
                                user_id=user_id,
                                action="create",
                                resource="transaction",
                                details={
                                    "transaction_id": transaction.id,
                                    "source": "mqtt_event",
                                    "mqtt_topic": settings.mqtt_topic,
                                    "email": event.correo_usuario,
                                    "card_id": card_id,
                                    "type": trans_data.type,
                                }
                            )
                            
                            logger.info(
                                "Transaction created from MQTT event",
                                extra={
                                    "details": {
                                        "event": "mqtt_transaction_created",
                                        "extra": {
                                            "transaction_id": transaction.id,
                                            "user_id": user_id,
                                            "card_id": card_id,
                                            "type": trans_data.type,
                                        }
                                    }
                                }
                            )
                            
                        except Exception as exc:
                            logger.error(
                                "Error creating transaction from MQTT event",
                                extra={
                                    "details": {
                                        "event": "mqtt_transaction_error",
                                        "extra": {
                                            "error": str(exc),
                                            "error_type": type(exc).__name__,
                                            "card_id": card_id,
                                        }
                                    }
                                }
                            )
                
                logger.info(
                    "MQTT event processing completed",
                    extra={
                        "details": {
                            "event": "mqtt_event_processed",
                            "extra": {"user_id": user_id}
                        }
                    }
                )
                
            except Exception as exc:
                logger.error(
                    "Error processing MQTT event",
                    extra={
                        "details": {
                            "event": "mqtt_event_error",
                            "extra": {"error": str(exc), "error_type": type(exc).__name__}
                        }
                    }
                )


# Global singleton instance
mqtt_listener_service = MqttListenerService()
