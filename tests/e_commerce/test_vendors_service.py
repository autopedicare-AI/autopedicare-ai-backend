import pytest
from uuid import uuid4
from fastapi import HTTPException
from app.services.e_commerce.vendors import VendorService
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.schemas.e_commerce.vendors import VendorCreate, VendorUpdate


@pytest.fixture
def test_user(db_session):
    user = User(
        email=f"vendor-tester-{uuid4().hex[:6]}@example.com",
        provider="google",
        provider_id=uuid4().hex,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def vendor_service(db_session, test_user):
    return VendorService(db_session, test_user)


def test_create_vendor_success(vendor_service, test_user):
    vendor_data = VendorCreate(
        name="Test Vendor Name",
        business_name="Test Business Name",
        address="456 Avenue",
        phone_number="0987654321",
    )
    response = vendor_service.create_vendor(vendor_data)

    assert response.name == "Test Vendor Name"
    assert response.business_name == "Test Business Name"
    assert str(response.owner_id) == str(test_user.id)
    assert response.verified is False  # Default should be False


def test_create_duplicate_vendor_fails(vendor_service):
    vendor_data = VendorCreate(
        name="Test Vendor",
        business_name="Test Business",
        address="456 Avenue",
        phone_number="0987654321",
    )
    # Create first one
    vendor_service.create_vendor(vendor_data)

    # Try creating again for same user
    with pytest.raises(HTTPException) as exc:
        vendor_service.create_vendor(vendor_data)
    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail or "already has" in exc.value.detail


def test_get_vendor_by_id(vendor_service):
    vendor_data = VendorCreate(
        name="My Store",
        business_name="Unique Business",
        address="Hidden Alley",
        phone_number="111222333",
    )
    vendor_service.create_vendor(vendor_data)

    response = vendor_service.get_vendor_by_id()
    assert response.name == "My Store"


def test_update_vendor(vendor_service):
    vendor_service.create_vendor(
        VendorCreate(
            name="Original Name",
            business_name="Original Business",
            address="Old St",
            phone_number="000",
        )
    )

    update_data = VendorUpdate(name="New Name", phone_number="999")
    response = vendor_service.update_vendor(update_data)

    assert response.name == "New Name"
    assert response.phone_number == "999"
    assert response.address == "Old St"  # Remained same


def test_delete_vendor(vendor_service, db_session, test_user):
    vendor_service.create_vendor(
        VendorCreate(
            name="To Be Deleted",
            business_name="To Delete Biz",
            address="Gone St",
            phone_number="X",
        )
    )

    vendor_service.delete_vendor()

    # Verify it's gone from service's perspective
    with pytest.raises(HTTPException) as exc:
        vendor_service.get_vendor_by_id()
    assert exc.value.status_code == 404
