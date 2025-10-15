import pytest
from app.crud.user import UserCRUD

@pytest.mark.asyncio
async def test_login_with_form(client, async_session):
    # Arrange: create a user
    user = await UserCRUD.create(
        async_session,
        name="Test User",
        phone="5550001",
        telegram_id=None,
        email="test@example.com",
        password="secret",
    )

    # Act: login via oauth2 form
    data = {"username": user.phone, "password": "secret"}
    res = await client.post("/auth/login", data=data)

    # Assert
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
