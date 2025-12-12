import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService
from app.services.parking_service import ParkingService
from app.utils.auth import create_access_token
import app.main as main_module


@pytest.fixture(autouse=True)
def setup_services():
    # Initialize services before each test
    main_module.auth_service = AuthService()
    main_module.parking_service = ParkingService()
    yield
    main_module.auth_service = None
    main_module.parking_service = None


@pytest.fixture
def client():
    # Test client fixture
    return TestClient(app)


@pytest.fixture
def auth_service():
    # Auth service fixture
    return AuthService()


@pytest.fixture
def parking_service():
    # Parking service fixture
    return ParkingService()


@pytest.fixture
def valid_token():
    # Get valid JWT token for testing
    token_data = {"sub": "user", "role": "user"}
    return create_access_token(token_data)


@pytest.fixture
def admin_token():
    # Get admin JWT token for testing
    token_data = {"sub": "admin", "role": "admin"}
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(valid_token):
    # Authorization headers with valid token
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def admin_headers(admin_token):
    # Authorization headers with admin token
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_reservation_data():
    # Sample reservation data for testing
    return {
        "mall_id": "pvj",
        "slot_id": "pvj-1",
        "user_name": "Test User",
        "vehicle_number": "B1234XYZ",
        "phone": "08123456789",
        "time_slot": {"start_time": "09:00", "end_time": "12:00"},
    }
