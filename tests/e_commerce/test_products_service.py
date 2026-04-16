import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException
from app.services.e_commerce.products import ProductService
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.models.e_commerce.products import Product
from app.schemas.e_commerce.products import ProductCreate, ProductUpdate


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"product-tester-{uuid4().hex[:6]}@example.com",
        provider="google",
        provider_id=uuid4().hex,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_vendor(db_session, test_user):
    vendor = Vendor(
        owner_id=test_user.id,
        name="Product Test Store",
        business_name=f"Prod Biz {uuid4().hex[:4]}",
        address="123 Street",
        phone_number="123456789",
        verified=True,
    )
    db_session.add(vendor)
    db_session.commit()
    return vendor


@pytest.fixture
def product_service(db_session, test_user):
    return ProductService(db_session, test_user)


def test_create_product_success(product_service, test_vendor):
    product_data = ProductCreate(
        name="Spark Plug",
        description="High quality",
        category="Engine",
        price=Decimal("15.99"),
        stock_quantity=100,
    )
    response = product_service.create_product(product_data)

    assert response.name == "Spark Plug"
    assert response.vendor_id == test_vendor.id
    assert response.is_active is True


def test_get_product_by_id(product_service, test_vendor, db_session):
    product = Product(
        vendor_id=test_vendor.id,
        name="Oil Filter",
        category="Engine",
        price=Decimal("10.00"),
        stock_quantity=50,
    )
    db_session.add(product)
    db_session.commit()

    # Pass UUID object directly instead of string
    response = product_service.get_product_by_id(product.id)
    assert response.name == "Oil Filter"


def test_update_product(product_service, test_vendor, db_session):
    product = Product(
        vendor_id=test_vendor.id,
        name="Old Belt",
        category="Transmission",
        price=Decimal("40.00"),
        stock_quantity=10,
    )
    db_session.add(product)
    db_session.commit()

    update_data = ProductUpdate(name="New Timing Belt", price=Decimal("55.00"))
    response = product_service.update_product(product.id, update_data)

    assert response.name == "New Timing Belt"
    assert response.price == Decimal("55.00")


def test_soft_delete_product(product_service, test_vendor, db_session):
    product = Product(
        vendor_id=test_vendor.id,
        name="Battery",
        category="Electrical",
        price=Decimal("120.00"),
        stock_quantity=5,
    )
    db_session.add(product)
    db_session.commit()

    product_service.delete_product(product.id)

    # Verify it's inactive
    db_session.refresh(product)
    assert product.is_active is False
