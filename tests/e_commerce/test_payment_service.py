import pytest
import hmac
import hashlib
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.payment.payment import PaystackService
from app.models.e_commerce.orders import Order, OrderStatus
from app.models.user import User


@pytest.fixture
def mock_user(db_session):
    user = User(
        email="test@example.com",
        provider="google",
        provider_id="12345",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def mock_order(db_session, mock_user):
    order = Order(
        user_id=mock_user.id,
        total_amount=100.0,
        status=OrderStatus.PENDING,
        payment_status="pending",
        shipping_address="123 Test St, Lagos, Nigeria",
    )
    db_session.add(order)
    db_session.commit()
    return order


@pytest.mark.asyncio
async def test_initialize_payment_success(db_session, mock_user, mock_order):
    service = PaystackService(db_session, current_user=mock_user)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "authorization_url": "https://paystack.com/authorize",
            "access_code": "code123",
        },
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await service.initialize_payment(mock_order.id)

        assert result["authorization_url"] == "https://paystack.com/authorize"
        assert "reference" in result

        # Verify DB update
        db_session.refresh(mock_order)
        assert mock_order.payment_reference is not None
        assert mock_order.authorization_url == "https://paystack.com/authorize"


@pytest.mark.asyncio
async def test_initialize_payment_existing_session(db_session, mock_user, mock_order):
    mock_order.payment_reference = "REF-123"
    mock_order.authorization_url = "https://existing.url"
    db_session.commit()

    service = PaystackService(db_session, current_user=mock_user)

    result = await service.initialize_payment(mock_order.id)

    assert result["reference"] == "REF-123"
    assert result["authorization_url"] == "https://existing.url"
    assert "Retrieved existing" in result["message"]


@pytest.mark.asyncio
async def test_verify_payment_success(db_session, mock_user, mock_order):
    mock_order.payment_reference = "REF-VERIFY"
    db_session.commit()

    service = PaystackService(db_session, current_user=mock_user)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": True,
        "data": {"status": "success", "reference": "REF-VERIFY", "amount": 10000},
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await service.verify_payment("REF-VERIFY")

        assert result["status"] == "paid"

        # Verify DB update
        db_session.refresh(mock_order)
        assert mock_order.payment_status == "paid"
        assert mock_order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_verify_payment_not_found(db_session, mock_user):
    service = PaystackService(db_session, current_user=mock_user)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": True, "data": {"status": "success"}}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(HTTPException) as exc:
            await service.verify_payment("NON-EXISTENT-REF")
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_process_webhook_success(db_session, mock_order):
    mock_order.payment_reference = "REF-WEBHOOK"
    db_session.commit()

    service = PaystackService(db_session)
    # Using a fake secret key for testing HMAC
    service.secret_key = "test_secret"

    payload_dict = {
        "event": "charge.success",
        "data": {"reference": "REF-WEBHOOK", "status": "success", "amount": 10000},
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    signature = hmac.new(
        key=b"test_secret", msg=payload_bytes, digestmod=hashlib.sha512
    ).hexdigest()

    result = await service.process_webhook(payload_bytes, signature)

    assert result["status"] == "success"

    db_session.refresh(mock_order)
    assert mock_order.payment_status == "paid"
    assert mock_order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_process_webhook_invalid_signature(db_session):
    service = PaystackService(db_session)
    service.secret_key = "test_secret"

    payload_bytes = b'{"event": "charge.success"}'
    invalid_signature = "wrong_signature"

    with pytest.raises(HTTPException) as exc:
        await service.process_webhook(payload_bytes, invalid_signature)

    assert exc.value.status_code == 400
    assert "Invalid signature" in exc.value.detail
