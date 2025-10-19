import pytest
from decimal import Decimal
from app.crud.user import UserCRUD
from datetime import date
from app.crud.bank import BankCRUD
from app.crud.card import CardCRUD
from app.crud.transaction import TransactionCRUD

@pytest.mark.asyncio
async def test_transfer_happy_path(client, async_session):
    # Arrange: user, two cards, and initial income on source
    user = await UserCRUD.create(
        async_session,
        name="TT",
        phone="5551001",
        telegram_id=None,
        email="tt@example.com",
        password="secret",
    )
    # auth: get token
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    bank = await BankCRUD.get_by_slug(async_session, "banregio")
    assert bank is not None

    src = await CardCRUD.create(
        async_session,
        user_id=user.id,
        bank_id=bank.id,
        type="debit",
        card_name="A",
        alias=None,
        billing_cycle_day=None,
        payment_due_day=None,
        grace_days=None,
    )
    dst = await CardCRUD.create(
        async_session,
        user_id=user.id,
        bank_id=bank.id,
        type="debit",
        card_name="B",
        alias=None,
        billing_cycle_day=None,
        payment_due_day=None,
        grace_days=None,
    )

    # seed income to source so it has balance
    await TransactionCRUD.create(
        async_session,
        user_id=user.id,
        card_id=src.id,
        description="seed",
        category_id=None,
        income=Decimal("150.00"),
        expenses=Decimal("0.00"),
        executed=True,
        operation_date=date.today(),
    )

    # Act: transfer 100 from src to dst
    payload = {
        "source_card_id": src.id,
        "destination_card_id": dst.id,
        "amount": "100.00",
        "description": "Move to B",
        "category_id": None,
        "operation_date": date.today().isoformat(),
    }
    res = await client.post("/transfers", json=payload, headers=headers)

    # Assert
    assert res.status_code == 201, res.text
    body = res.json()
    stx = body["source_transaction"]
    dtx = body["destination_transaction"]
    assert stx["transfer_id"] == dtx["transfer_id"]
    assert Decimal(str(stx["expenses"])) == Decimal("100.00")
    assert Decimal(str(dtx["income"])) == Decimal("100.00")
