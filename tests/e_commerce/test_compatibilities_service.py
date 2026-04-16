import pytest
from uuid import uuid4, UUID
from decimal import Decimal
from fastapi import HTTPException
from app.services.e_commerce.compatibilities import CompatibilityService
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.models.e_commerce.products import Product
from app.models.e_commerce.compatibility import Compatibility
from app.schemas.e_commerce.compatibility import CompatibilityCreate


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"compat-tester-{uuid4().hex[:6]}@example.com",
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
        name="Compatibility Test Store",
        business_name=f"Comp Biz {uuid4().hex[:4]}",
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
        name="Brake Pad P1",
        category="Brakes",
        price=Decimal("45.00"),
        stock_quantity=20,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def compatibility_service(db_session, test_user, test_vendor):
    return CompatibilityService(db_session, test_user)


def test_create_compatibility(compatibility_service, test_product, db_session):
    # CompatibilityCreate no longer expects vendor_id or notes
    compat_data = CompatibilityCreate(
        product_id=test_product.id,
        car_brand="Toyota",
        car_model="Camry",
        year="2020",
        engine_type="V6",
        is_active=True,
    )
    response = compatibility_service.create_compatibility(compat_data)

    assert response.car_brand == "Toyota"
    assert response.product_id == test_product.id


def test_match_ai_identified_part_exact(
    compatibility_service, test_product, db_session
):
    # Setup compatibility
    compat = Compatibility(
        product_id=test_product.id,
        vendor_id=test_product.vendor_id,
        car_brand="Toyota",
        car_model="Camry",
        year="2020",
        engine_type="V6",
    )
    db_session.add(compat)
    db_session.commit()

    # Search for something that matches the name exactly
    results = compatibility_service.match_ai_identified_part(
        ai_label="Brake Pad P1", car_brand="Toyota", car_model="Camry", year="2020"
    )

    assert results["identified_as"] == "Brake Pad P1"
    assert len(results["exact_matches"]) == 1
    assert results["exact_matches"][0].name == "Brake Pad P1"


def test_match_ai_identified_part_out_of_stock(
    db_session, compatibility_service, test_product
):
    # Setup compatibility for exact match which will be OOS
    compat = Compatibility(
        product_id=test_product.id,
        vendor_id=test_product.vendor_id,
        car_brand="Toyota",
        car_model="Camry",
        year="2020",
    )
    db_session.add(compat)

    # Set stock to 0 for the exact match item
    test_product.stock_quantity = 0
    db_session.add(test_product)

    # Add an alternative match:
    # Use a category and name that won't trigger 'is_exact_match' if the label is "P1"
    alt_product = Product(
        vendor_id=test_product.vendor_id,
        name="Generic Disc",
        category="Wheels",
        price=Decimal("30.00"),
        stock_quantity=5,
        is_active=True,
    )
    db_session.add(alt_product)
    db_session.flush()

    alt_compat = Compatibility(
        product_id=alt_product.id,
        vendor_id=test_product.vendor_id,
        car_brand="Toyota",
        car_model="Camry",
        year="2020",
    )
    db_session.add(alt_compat)
    db_session.commit()

    # Search for "P1" - this matches "Brake Pad P1" (exact, but OOS)
    # but doesn't match "Generic Disc" (alternative)
    results = compatibility_service.match_ai_identified_part(
        ai_label="P1", car_brand="Toyota", car_model="Camry", year="2020"
    )

    # Message should indicate exact match is out of stock and alternatives are shown
    assert "out of stock" in results["message"].lower()
    assert len(results["exact_matches"]) == 0
    assert len(results["alternative_matches"]) == 1
