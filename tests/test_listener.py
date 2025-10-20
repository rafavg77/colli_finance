import pytest
from app.crud.user import UserCRUD
from app.crud.bank import BankCRUD
from app.crud.card import CardCRUD
from app.crud.listener import ListenerCredCRUD, ListenerTemplateCRUD, ListenerConfigCRUD
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_listener_credentials(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550101",
        telegram_id=None,
        email="listener1@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "status": "enabled",
        "google_credentials": {"key": "value"},
        "google_access_token": {"token": "abc123"}
    }
    
    # Act
    res = await client.post("/listener/credentials", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "enabled"
    assert body["user_id"] == user.id


@pytest.mark.asyncio
async def test_get_my_credentials(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550102",
        telegram_id=None,
        email="listener2@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create credentials
    await ListenerCredCRUD.create(
        async_session,
        user_id=user.id,
        status="disabled",
        google_credentials=None,
        google_access_token=None
    )
    
    # Act
    res = await client.get("/listener/credentials", headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert body["user_id"] == user.id
    assert body["status"] == "disabled"


@pytest.mark.asyncio
async def test_update_credentials(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550103",
        telegram_id=None,
        email="listener3@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    await ListenerCredCRUD.create(
        async_session,
        user_id=user.id,
        status="disabled",
    )
    
    payload = {"status": "enabled"}
    
    # Act
    res = await client.patch("/listener/credentials", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "enabled"


@pytest.mark.asyncio
async def test_delete_credentials(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550104",
        telegram_id=None,
        email="listener4@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    await ListenerCredCRUD.create(
        async_session,
        user_id=user.id,
        status="disabled",
    )
    
    # Act
    res = await client.delete("/listener/credentials", headers=headers)
    
    # Assert
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_create_listener_template(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550105",
        telegram_id=None,
        email="listener5@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    bank = await BankCRUD.create(
        async_session,
        name="TestBank",
        slug="test-bank-listener",
        display_name="Test Bank",
        is_active=True
    )
    
    payload = {
        "bank_id": bank.id,
        "template_code": "TEMPLATE001",
        "email_sender": "noreply@bank.com",
        "subject_pattern": "Transaction Alert",
        "amount_pattern": "\\$([0-9.]+)",
        "transaction_type": "expense",
        "is_active": True
    }
    
    # Act
    res = await client.post("/listener/templates", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 201
    body = res.json()
    assert body["bank_id"] == bank.id
    assert body["template_code"] == "TEMPLATE001"


@pytest.mark.asyncio
async def test_list_templates(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550106",
        telegram_id=None,
        email="listener6@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    bank = await BankCRUD.create(
        async_session,
        name="ListBank",
        slug="list-bank",
        display_name="List Bank",
        is_active=True
    )
    
    await ListenerTemplateCRUD.create(
        async_session,
        bank_id=bank.id,
        template_code="CODE1",
        email_sender="sender@bank.com",
        transaction_type="income",
        is_active=True
    )
    
    # Act
    res = await client.get(f"/listener/templates?bank_id={bank.id}", headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["template_code"] == "CODE1"


@pytest.mark.asyncio
async def test_create_listener_config(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550107",
        telegram_id=None,
        email="listener7@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create credential
    cred = await ListenerCredCRUD.create(
        async_session,
        user_id=user.id,
        status="enabled",
    )
    
    # Create bank and template
    bank = await BankCRUD.create(
        async_session,
        name="ConfigBank",
        slug="config-bank",
        display_name="Config Bank",
        is_active=True
    )
    
    template = await ListenerTemplateCRUD.create(
        async_session,
        bank_id=bank.id,
        template_code="TMPL1",
        email_sender="sender@bank.com",
        transaction_type="expense",
        is_active=True
    )
    
    # Create card
    card = await CardCRUD.create(
        async_session,
        user_id=user.id,
        bank_id=bank.id,
        type="credit",
        card_name="Test Card",
        billing_cycle_day=1,
        payment_due_day=15,
    )
    
    payload = {
        "listener_cred_id": cred.id,
        "listener_template_id": template.id,
        "card_id": card.id,
        "is_active": True
    }
    
    # Act
    res = await client.post("/listener/configs", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 201
    body = res.json()
    assert body["listener_cred_id"] == cred.id
    assert body["listener_template_id"] == template.id
    assert body["card_id"] == card.id


@pytest.mark.asyncio
async def test_list_configs_by_card(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550108",
        telegram_id=None,
        email="listener8@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    cred = await ListenerCredCRUD.create(
        async_session,
        user_id=user.id,
        status="enabled",
    )
    
    bank = await BankCRUD.create(
        async_session,
        name="CardBank",
        slug="card-bank",
        display_name="Card Bank",
        is_active=True
    )
    
    template = await ListenerTemplateCRUD.create(
        async_session,
        bank_id=bank.id,
        template_code="TMPL2",
        email_sender="sender@bank.com",
        transaction_type="expense",
        is_active=True
    )
    
    card = await CardCRUD.create(
        async_session,
        user_id=user.id,
        bank_id=bank.id,
        type="debit",
        card_name="Test Debit",
    )
    
    await ListenerConfigCRUD.create(
        async_session,
        listener_cred_id=cred.id,
        listener_template_id=template.id,
        card_id=card.id,
        is_active=True
    )
    
    # Act
    res = await client.get(f"/listener/configs?card_id={card.id}", headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["card_id"] == card.id
