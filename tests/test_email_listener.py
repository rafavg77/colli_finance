import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.email_listener import EmailListenerService


def test_email_listener_service_initialization():
    """Test email listener service initialization"""
    service = EmailListenerService()
    assert service.running is False
    assert service.thread is None
    assert service.mqtt_client is None


def test_email_listener_disabled_by_config():
    """Test that email listener does not start when disabled in config"""
    with patch('app.services.email_listener.settings') as mock_settings:
        mock_settings.email_listener_enabled = False
        
        service = EmailListenerService()
        service.start()
        
        assert service.running is False
        assert service.thread is None


def test_extract_transaction_data_with_amount():
    """Test extracting transaction data from email content"""
    service = EmailListenerService()
    
    # Mock template with patterns
    template = Mock()
    template.amount_pattern = r'\$([0-9,.]+)'
    template.description_pattern = r'at (.+?)$'
    template.date_pattern = None
    
    subject = "Transaction Alert"
    body = "You spent $100.50 at Test Store"
    
    data = service._extract_transaction_data(template, subject, body)
    
    assert data is not None
    assert data['amount'] == '100.50'
    assert 'description' in data


def test_extract_transaction_data_no_amount():
    """Test that extraction fails when no amount is found"""
    service = EmailListenerService()
    
    template = Mock()
    template.amount_pattern = r'\$([0-9,.]+)'
    template.description_pattern = None
    
    subject = "Transaction Alert"
    body = "No amount in this email"
    
    data = service._extract_transaction_data(template, subject, body)
    
    assert data is None


def test_get_email_body_plain_text():
    """Test extracting plain text email body"""
    import base64
    
    service = EmailListenerService()
    
    # Mock payload with plain text
    text_content = "This is the email body"
    encoded_data = base64.urlsafe_b64encode(text_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        'mimeType': 'text/plain',
        'body': {
            'data': encoded_data
        }
    }
    
    body = service._get_email_body(payload)
    assert body == text_content


def test_publish_transaction_event_income():
    """Test publishing income transaction event to MQTT"""
    with patch('app.services.email_listener.settings') as mock_settings:
        mock_settings.mqtt_topic = "test/topic"
        
        service = EmailListenerService()
        service.mqtt_client = Mock()
        service.mqtt_client.publish = Mock(return_value=Mock(rc=0))  # MQTT_ERR_SUCCESS
        
        transaction_data = {
            'amount': '100.00',
            'description': 'Test income'
        }
        
        service._publish_transaction_event(
            user_id=1,
            user_email="test@example.com",
            card_id=1,
            transaction_data=transaction_data,
            transaction_type='income'
        )
        
        # Verify publish was called
        assert service.mqtt_client.publish.called
        call_args = service.mqtt_client.publish.call_args
        
        # Verify payload structure
        import json
        payload = json.loads(call_args[0][1])
        
        assert payload['id_usuario'] == 1
        assert payload['correo_usuario'] == "test@example.com"
        assert len(payload['tarjetas']) == 1
        assert payload['tarjetas'][0]['id_tarjeta'] == 1
        assert len(payload['tarjetas'][0]['transaction']) == 1
        
        transaction = payload['tarjetas'][0]['transaction'][0]
        assert transaction['income'] == '100.00'
        assert transaction['expense'] == ''
        assert transaction['type'] == 'income'


def test_publish_transaction_event_expense():
    """Test publishing expense transaction event to MQTT"""
    with patch('app.services.email_listener.settings') as mock_settings:
        mock_settings.mqtt_topic = "test/topic"
        
        service = EmailListenerService()
        service.mqtt_client = Mock()
        service.mqtt_client.publish = Mock(return_value=Mock(rc=0))
        
        transaction_data = {
            'amount': '50.00',
            'description': 'Test expense'
        }
        
        service._publish_transaction_event(
            user_id=1,
            user_email="test@example.com",
            card_id=2,
            transaction_data=transaction_data,
            transaction_type='expense'
        )
        
        # Verify payload
        import json
        call_args = service.mqtt_client.publish.call_args
        payload = json.loads(call_args[0][1])
        
        transaction = payload['tarjetas'][0]['transaction'][0]
        assert transaction['income'] == ''
        assert transaction['expense'] == '50.00'
        assert transaction['type'] == 'expense'


def test_service_stop_when_not_running():
    """Test that stop() works when service is not running"""
    service = EmailListenerService()
    service.stop()  # Should not raise any error
    assert service.running is False
