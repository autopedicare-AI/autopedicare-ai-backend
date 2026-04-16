import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException
from app.services.e_commerce.orders import OrderService
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.models.e_commerce.products import Product
from app.models.e_commerce.carts import Cart, CartItem
from app.schemas.e_commerce.orders import OrderCreate


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"order-tester-{uuid4().hex[:6]}@example.com",
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
        name="Order Test Store",
        business_name=f"Order Biz {uuid4().hex[:4]}",
        address="123 Street",
        phone_number="123456789",
        verified=True,
    )
    db_session.add(vendor)
    db_session.commit()
    return vendor


@pytest.fixture
def test_product(db_session, test_vendor):
    product = Product(
        vendor_id=test_vendor.id,
        name="Brake Pad",
        category="Brakes",
        price=Decimal("150.00"),
        stock_quantity=5,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def order_service(db_session, test_user):
    return OrderService(db_session, test_user)


def test_checkout_success(db_session, order_service, test_user, test_product):
    # Setup cart
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    db_session.flush()

    cart_item = CartItem(cart_id=cart.id, product_id=test_product.id, quantity=2)
    db_session.add(cart_item)
    db_session.commit()

    order_data = OrderCreate(shipping_address="456 Delivery Rd")
    response = order_service.checkout(order_data)

    assert response.total_amount == Decimal("300.00")
    assert response.status == "pending"
    assert len(response.items) == 1
    assert response.items[0].product_id == test_product.id

    # Verify stock deducted
    db_session.refresh(test_product)
    assert test_product.stock_quantity == 3

    # Verify cart cleared
    cart_count = db_session.query(CartItem).filter(CartItem.cart_id == cart.id).count()
    assert cart_count == 0


def test_checkout_empty_cart_fails(order_service, test_user, db_session):
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        order_service.checkout(OrderCreate(shipping_address="Home"))
    assert exc.value.status_code == 400
    assert "Cart is empty" in exc.value.detail


def test_checkout_insufficient_stock_fails(
    db_session, order_service, test_user, test_product
):
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    db_session.flush()

    cart_item = CartItem(
        cart_id=cart.id, product_id=test_product.id, quantity=10
    )  # More than stock (5)
    db_session.add(cart_item)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        order_service.checkout(OrderCreate(shipping_address="Home"))
    assert exc.value.status_code == 400
    assert "Not enough stock" in exc.value.detail
