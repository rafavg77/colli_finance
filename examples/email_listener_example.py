#!/usr/bin/env python3
"""
Example script to test the Email Listener Service

This script demonstrates how to set up and test the email listener service
that monitors Gmail inbox and publishes transaction events to MQTT.

Usage:
    python examples/email_listener_example.py

Prerequisites:
    1. Configure Google OAuth credentials in listener_cred table
    2. Set up listener templates for your banks
    3. Configure listener configs to link templates with cards
    4. Start MQTT broker (mosquitto)
    5. Enable EMAIL_LISTENER_ENABLED=true in .env
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.email_listener import email_listener_service
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


def main():
    """Main function to test email listener"""
    
    print("=" * 60)
    print("Email Listener Service Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  Email Listener Enabled: {settings.email_listener_enabled}")
    print(f"  Poll Interval: {settings.email_listener_poll_interval} seconds")
    print(f"  Max Results: {settings.email_listener_max_results}")
    print(f"  MQTT Broker: {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
    print(f"  MQTT Topic: {settings.mqtt_topic}")
    print()
    
    if not settings.email_listener_enabled:
        print("⚠️  Email listener is disabled in configuration.")
        print("   Set EMAIL_LISTENER_ENABLED=true in your .env file")
        return
    
    if not settings.mqtt_broker_host:
        print("⚠️  MQTT broker is not configured.")
        print("   Set MQTT_BROKER_HOST in your .env file")
        return
    
    print("Starting email listener service...")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Start the service
        email_listener_service.start()
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping email listener service...")
        email_listener_service.stop()
        print("Service stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        email_listener_service.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
