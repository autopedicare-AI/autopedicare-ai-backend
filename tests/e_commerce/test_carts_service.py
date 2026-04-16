import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException
from app.services.e_commerce.carts import CartService
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.models.e_commerce.products import Product
from app.schemas.e_commerce.carts import CartItemCreate, CartItemUpdate


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"tester-{uuid4().hex[:6]}@example.com",
        provider="google",
        provider_id=uuid4().hex,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_vendor(db_session, test_user):
    vendor = Vendor(
        owner_id=test_user.id,
        name="Test Store",
        business_name=f"Test Business {uuid4().hex[:4]}",
        address="123 Street",
        phone_number="123456789",
        verified=True,
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor


@pytest.fixture
def test_product(db_session, test_vendor):
    product = Product(
        vendor_id=test_vendor.id,
        name="Test Wiper",
        category="Exterior",
        price=Decimal("25.50"),
        stock_quantity=10,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def cart_service(db_session, test_user):
    return CartService(db_session, test_user)


def test_view_cart_initial(cart_service):
    response = cart_service.view_cart()
    assert response["total_amount"] == 0.0
    assert len(response["items"]) == 0


def test_add_to_cart_new_item(cart_service, test_product):
    cart_data = CartItemCreate(product_id=test_product.id, quantity=2)
    response = cart_service.add_to_cart(cart_data)

    assert float(response["total_amount"]) == 51.0
    assert len(response["items"]) == 1
    assert response["items"][0]["product_name"] == "Test Wiper"
    assert response["items"][0]["quantity"] == 2


def test_add_to_cart_existing_item(cart_service, test_product):
    # Add first time
    cart_service.add_to_cart(CartItemCreate(product_id=test_product.id, quantity=2))
    # Add second time (should increment)
    response = cart_service.add_to_cart(
        CartItemCreate(product_id=test_product.id, quantity=3)
    )

    assert response["items"][0]["quantity"] == 5
    assert float(response["total_amount"]) == 127.5


def test_add_to_cart_insufficient_stock(cart_service, test_product):
    with pytest.raises(HTTPException) as exc:
        cart_service.add_to_cart(
            CartItemCreate(product_id=test_product.id, quantity=11)
        )
    assert exc.value.status_code == 400
    assert "Only 10 more units" in exc.value.detail


def test_update_cart_item(cart_service, test_product):
    cart_service.add_to_cart(CartItemCreate(product_id=test_product.id, quantity=2))
    item_id = cart_service.view_cart()["items"][0]["id"]

    # Passing raw UUID object instead of string
    response = cart_service.update_cart_item(item_id, CartItemUpdate(quantity=5))
    assert response["items"][0]["quantity"] == 5


def test_remove_cart_item(cart_service, test_product):
    cart_service.add_to_cart(CartItemCreate(product_id=test_product.id, quantity=2))
    item_id = cart_service.view_cart()["items"][0]["id"]

    # Passing raw UUID object instead of string
    response = cart_service.remove_cart_item(item_id)
    assert len(response["items"]) == 0
    assert response["total_amount"] == 0.0
