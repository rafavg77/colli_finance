import pytest
from app.crud.user import UserCRUD
from app.crud.bank import BankCRUD
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_list_banks(client, async_session):
    # Arrange: create user and get token
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550001",
        telegram_id=None,
        email="test@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Act
    res = await client.get("/banks", headers=headers)
    
    # Assert
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_create_bank(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550002",
        telegram_id=None,
        email="test2@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Test Bank",
        "slug": "test-bank",
        "display_name": "Test Bank Display",
        "is_active": True
    }
    
    # Act
    res = await client.post("/banks", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Test Bank"
    assert body["slug"] == "test-bank"


@pytest.mark.asyncio
async def test_create_duplicate_bank_slug(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550003",
        telegram_id=None,
        email="test3@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create first bank
    await BankCRUD.create(
        async_session,
        name="Bank1",
        slug="duplicate-slug",
        display_name="Bank One",
        is_active=True
    )
    
    payload = {
        "name": "Bank2",
        "slug": "duplicate-slug",
        "display_name": "Bank Two",
        "is_active": True
    }
    
    # Act
    res = await client.post("/banks", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 400
    assert "ya existe" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_bank(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550004",
        telegram_id=None,
        email="test4@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    bank = await BankCRUD.create(
        async_session,
        name="GetBank",
        slug="get-bank",
        display_name="Get Bank",
        is_active=True
    )
    
    # Act
    res = await client.get(f"/banks/{bank.id}", headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == bank.id
    assert body["name"] == "GetBank"


@pytest.mark.asyncio
async def test_update_bank(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550005",
        telegram_id=None,
        email="test5@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    bank = await BankCRUD.create(
        async_session,
        name="UpdateBank",
        slug="update-bank",
        display_name="Update Bank",
        is_active=True
    )
    
    payload = {
        "name": "Updated Bank",
        "slug": "update-bank",
        "display_name": "Updated Display",
        "is_active": False
    }
    
    # Act
    res = await client.patch(f"/banks/{bank.id}", json=payload, headers=headers)
    
    # Assert
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Updated Bank"
    assert body["is_active"] is False


@pytest.mark.asyncio
async def test_delete_bank(client, async_session):
    # Arrange
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550006",
        telegram_id=None,
        email="test6@example.com",
        password="secret",
    )
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    bank = await BankCRUD.create(
        async_session,
        name="DeleteBank",
        slug="delete-bank",
        display_name="Delete Bank",
        is_active=True
    )
    
    # Act
    res = await client.delete(f"/banks/{bank.id}", headers=headers)
    
    # Assert
    assert res.status_code == 204
    
    # Verify deleted
    deleted = await BankCRUD.get_by_id(async_session, bank.id)
    assert deleted is None
