import asyncio
import json
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import paho.mqtt.client as mqtt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.crud.card import CardCRUD
from app.crud.listener import ListenerConfigCRUD, ListenerCredCRUD, ListenerTemplateCRUD
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)
settings = get_settings()


class EmailListenerService:
    """Service to monitor Gmail inbox and publish transaction events to MQTT"""
    
    def __init__(self):
        self.running = False
        self.thread: threading.Thread | None = None
        self.mqtt_client: mqtt.Client | None = None
        
    def start(self):
        """Start email listener in a separate thread"""
        if self.running:
            logger.warning("Email listener already running")
            return
            
        if not settings.email_listener_enabled:
            logger.info("Email listener is disabled in configuration")
            return
            
        if not settings.mqtt_broker_host:
            logger.warning("MQTT broker not configured, email listener cannot publish events")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_email_listener, daemon=True)
        self.thread.start()
        logger.info(
            "Email listener service started",
            extra={
                "details": {
                    "event": "email_listener_start",
                    "extra": {
                        "poll_interval": settings.email_listener_poll_interval,
                        "max_results": settings.email_listener_max_results,
                    }
                }
            }
        )
    
    def stop(self):
        """Stop email listener"""
        if not self.running:
            return
            
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Email listener service stopped")
    
    def _run_email_listener(self):
        """Run email listener in a blocking loop"""
        try:
            # Initialize MQTT client for publishing
            self._init_mqtt_client()
            
            while self.running:
                try:
                    asyncio.run(self._check_emails())
                except Exception as exc:
                    logger.error(
                        "Error checking emails",
                        extra={
                            "details": {
                                "event": "email_check_error",
                                "extra": {"error": str(exc), "error_type": type(exc).__name__}
                            }
                        }
                    )
                
                # Wait before next check
                time.sleep(settings.email_listener_poll_interval)
                
        except Exception as exc:
            logger.error(
                "Error in email listener loop",
                extra={
                    "details": {
                        "event": "email_listener_error",
                        "extra": {"error": str(exc), "error_type": type(exc).__name__}
                    }
                }
            )
    
    def _init_mqtt_client(self):
        """Initialize MQTT client for publishing events"""
        try:
            self.mqtt_client = mqtt.Client()
            
            # Set credentials if provided
            if settings.mqtt_username and settings.mqtt_password:
                self.mqtt_client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
            
            # Connect to broker
            self.mqtt_client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=60)
            self.mqtt_client.loop_start()
            
            logger.info(
                "MQTT client initialized for email listener",
                extra={
                    "details": {
                        "event": "email_listener_mqtt_init",
                        "extra": {"broker": settings.mqtt_broker_host}
                    }
                }
            )
        except Exception as exc:
            logger.error(
                "Failed to initialize MQTT client",
                extra={
                    "details": {
                        "event": "mqtt_init_error",
                        "extra": {"error": str(exc), "error_type": type(exc).__name__}
                    }
                }
            )
            raise
    
    async def _check_emails(self):
        """Check emails for all active listener credentials"""
        async with AsyncSessionLocal() as db:
            # Get all active listener credentials
            creds = await ListenerCredCRUD.list_all(db)
            
            for listener_cred in creds:
                if listener_cred.status != "enabled":
                    continue
                    
                try:
                    await self._process_user_emails(db, listener_cred)
                except Exception as exc:
                    logger.error(
                        "Error processing user emails",
                        extra={
                            "details": {
                                "event": "user_email_processing_error",
                                "extra": {
                                    "user_id": listener_cred.user_id,
                                    "error": str(exc),
                                    "error_type": type(exc).__name__
                                }
                            }
                        }
                    )
    
    async def _process_user_emails(self, db, listener_cred):
        """Process emails for a specific user"""
        # Get user configurations
        from app.crud.listener import ListenerConfigCRUD
        from sqlalchemy import select
        from app.db.models import ListenerConfig
        
        result = await db.execute(
            select(ListenerConfig)
            .where(
                ListenerConfig.listener_cred_id == listener_cred.id,
                ListenerConfig.is_active == True
            )
        )
        configs = list(result.scalars().all())
        
        if not configs:
            logger.debug(
                "No active configurations for user",
                extra={
                    "details": {
                        "event": "no_active_configs",
                        "extra": {"user_id": listener_cred.user_id}
                    }
                }
            )
            return
        
        # Build Gmail service
        gmail_service = self._build_gmail_service(listener_cred)
        if not gmail_service:
            return
        
        # Get user email for logging
        try:
            profile = gmail_service.users().getProfile(userId='me').execute()
            user_email = profile.get('emailAddress', 'unknown')
        except Exception as exc:
            logger.error(
                "Failed to get user profile",
                extra={
                    "details": {
                        "event": "gmail_profile_error",
                        "extra": {"error": str(exc)}
                    }
                }
            )
            user_email = "unknown"
        
        # Check for new emails (last hour)
        after_timestamp = int((datetime.now() - timedelta(hours=1)).timestamp())
        query = f'after:{after_timestamp}'
        
        try:
            results = gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=settings.email_listener_max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            logger.info(
                "Fetched emails for user",
                extra={
                    "details": {
                        "event": "emails_fetched",
                        "extra": {
                            "user_id": listener_cred.user_id,
                            "email": user_email,
                            "message_count": len(messages)
                        }
                    }
                }
            )
            
            # Process each message
            for message in messages:
                await self._process_email_message(
                    db, gmail_service, message['id'], 
                    configs, listener_cred.user_id, user_email
                )
                
        except Exception as exc:
            logger.error(
                "Error fetching emails",
                extra={
                    "details": {
                        "event": "gmail_fetch_error",
                        "extra": {
                            "user_id": listener_cred.user_id,
                            "error": str(exc),
                            "error_type": type(exc).__name__
                        }
                    }
                }
            )
    
    def _build_gmail_service(self, listener_cred):
        """Build Gmail API service from credentials"""
        try:
            if not listener_cred.google_access_token:
                logger.warning(
                    "No Google access token found",
                    extra={
                        "details": {
                            "event": "no_access_token",
                            "extra": {"user_id": listener_cred.user_id}
                        }
                    }
                )
                return None
            
            # Build credentials from stored token
            creds = Credentials.from_authorized_user_info(
                listener_cred.google_access_token,
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            # Refresh if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # TODO: Update stored token in database
            
            # Build service
            service = build('gmail', 'v1', credentials=creds)
            return service
            
        except Exception as exc:
            logger.error(
                "Failed to build Gmail service",
                extra={
                    "details": {
                        "event": "gmail_service_error",
                        "extra": {
                            "user_id": listener_cred.user_id,
                            "error": str(exc),
                            "error_type": type(exc).__name__
                        }
                    }
                }
            )
            return None
    
    async def _process_email_message(self, db, gmail_service, message_id, configs, user_id, user_email):
        """Process a single email message"""
        try:
            # Get full message
            message = gmail_service.users().messages().get(
                userId='me', 
                id=message_id, 
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            sender = headers.get('From', '')
            subject = headers.get('Subject', '')
            
            # Extract body
            body = self._get_email_body(message['payload'])
            
            logger.debug(
                "Processing email",
                extra={
                    "details": {
                        "event": "email_processing",
                        "extra": {
                            "message_id": message_id,
                            "sender": sender,
                            "subject": subject[:50]
                        }
                    }
                }
            )
            
            # Try to match with templates
            for config in configs:
                await self._try_match_template(
                    db, config, sender, subject, body, 
                    user_id, user_email, message_id
                )
                
        except Exception as exc:
            logger.error(
                "Error processing email message",
                extra={
                    "details": {
                        "event": "email_message_error",
                        "extra": {
                            "message_id": message_id,
                            "error": str(exc),
                            "error_type": type(exc).__name__
                        }
                    }
                }
            )
    
    def _get_email_body(self, payload):
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in payload and 'data' in payload['body']:
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body
    
    async def _try_match_template(self, db, config, sender, subject, body, user_id, user_email, message_id):
        """Try to match email with template and extract transaction data"""
        # Get template
        template = await ListenerTemplateCRUD.get_by_id(db, config.listener_template_id)
        if not template or not template.is_active:
            return
        
        # Check sender match
        if template.email_sender and template.email_sender.lower() not in sender.lower():
            return
        
        # Check subject pattern if specified
        if template.subject_pattern:
            if not re.search(template.subject_pattern, subject, re.IGNORECASE):
                return
        
        logger.info(
            "Email matched template",
            extra={
                "details": {
                    "event": "template_matched",
                    "extra": {
                        "template_id": template.id,
                        "template_code": template.template_code,
                        "message_id": message_id
                    }
                }
            }
        )
        
        # Extract transaction data
        transaction_data = self._extract_transaction_data(template, subject, body)
        
        if transaction_data:
            # Get card details
            card = await CardCRUD.get_by_id(db, config.card_id, user_id)
            if not card:
                logger.warning(
                    "Card not found for transaction",
                    extra={
                        "details": {
                            "event": "card_not_found",
                            "extra": {"card_id": config.card_id}
                        }
                    }
                )
                return
            
            # Publish to MQTT
            self._publish_transaction_event(
                user_id, user_email, config.card_id, 
                transaction_data, template.transaction_type
            )
    
    def _extract_transaction_data(self, template, subject, body):
        """Extract transaction data from email using template patterns"""
        data = {}
        
        # Combine subject and body for pattern matching
        content = f"{subject}\n{body}"
        
        # Extract amount
        if template.amount_pattern:
            amount_match = re.search(template.amount_pattern, content, re.IGNORECASE)
            if amount_match:
                # Try to get first capturing group or full match
                data['amount'] = amount_match.group(1) if len(amount_match.groups()) > 0 else amount_match.group(0)
                # Clean amount (remove currency symbols, commas)
                data['amount'] = re.sub(r'[^\d.]', '', data['amount'])
        
        # Extract description
        if template.description_pattern:
            desc_match = re.search(template.description_pattern, content, re.IGNORECASE)
            if desc_match:
                data['description'] = desc_match.group(1) if len(desc_match.groups()) > 0 else desc_match.group(0)
        else:
            # Use subject as description if no pattern
            data['description'] = subject[:100]
        
        # Extract date
        if template.date_pattern:
            date_match = re.search(template.date_pattern, content, re.IGNORECASE)
            if date_match:
                data['date'] = date_match.group(1) if len(date_match.groups()) > 0 else date_match.group(0)
        
        # If we don't have amount, skip
        if 'amount' not in data or not data['amount']:
            logger.debug(
                "Could not extract amount from email",
                extra={
                    "details": {
                        "event": "amount_extraction_failed",
                        "extra": {"template_id": template.id}
                    }
                }
            )
            return None
        
        return data
    
    def _publish_transaction_event(self, user_id, user_email, card_id, transaction_data, transaction_type):
        """Publish transaction event to MQTT broker"""
        try:
            # Parse operation date
            operation_date = datetime.now().date().isoformat()
            if 'date' in transaction_data:
                try:
                    # Try to parse date - this is simplified, real implementation should handle various formats
                    operation_date = transaction_data['date']
                except Exception:
                    pass
            
            # Prepare MQTT event payload
            event = {
                "id_usuario": user_id,
                "correo_usuario": user_email,
                "tarjetas": [
                    {
                        "id_tarjeta": card_id,
                        "transaction": [
                            {
                                "amount": transaction_data.get('amount', ''),
                                "description": transaction_data.get('description', 'Email transaction'),
                                "income": transaction_data['amount'] if transaction_type == 'income' else "",
                                "expense": transaction_data['amount'] if transaction_type == 'expense' else "",
                                "type": transaction_type,
                                "operation_date": operation_date
                            }
                        ]
                    }
                ]
            }
            
            # Publish to MQTT
            payload = json.dumps(event)
            result = self.mqtt_client.publish(settings.mqtt_topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(
                    "Transaction event published to MQTT",
                    extra={
                        "details": {
                            "event": "transaction_published",
                            "extra": {
                                "user_id": user_id,
                                "card_id": card_id,
                                "type": transaction_type,
                                "amount": transaction_data['amount']
                            }
                        }
                    }
                )
            else:
                logger.error(
                    "Failed to publish transaction event",
                    extra={
                        "details": {
                            "event": "mqtt_publish_error",
                            "extra": {"return_code": result.rc}
                        }
                    }
                )
                
        except Exception as exc:
            logger.error(
                "Error publishing transaction event",
                extra={
                    "details": {
                        "event": "publish_error",
                        "extra": {
                            "error": str(exc),
                            "error_type": type(exc).__name__
                        }
                    }
                }
            )


# Global singleton instance
email_listener_service = EmailListenerService()
