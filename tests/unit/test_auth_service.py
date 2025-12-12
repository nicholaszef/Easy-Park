
import pytest
from app.services.auth_service import AuthService


class TestAuthService:

    # Test users_db initialization
    def test_init_users_db(self, auth_service):
        users = auth_service.get_all_users()
        assert len(users) == 2
        assert any(u["username"] == "user" for u in users)
        assert any(u["username"] == "admin" for u in users)

    # Test get user that exists
    def test_get_user_exists(self, auth_service):
        user = auth_service.get_user("user")
        assert user is not None
        assert user["username"] == "user"
        assert user["role"] == "user"

    # Test get user that does not exist
    def test_get_user_not_exists(self, auth_service):
        user = auth_service.get_user("nonexistent")
        assert user is None

    # Test successful authentication
    def test_authenticate_user_success(self, auth_service):
        user = auth_service.authenticate_user("user", "12345")
        assert user is not None
        assert user["username"] == "user"

    # Test authentication with wrong password
    def test_authenticate_user_wrong_password(self, auth_service):
        user = auth_service.authenticate_user("user", "wrongpassword")
        assert user is None

    # Test authentication for non-existent user
    def test_authenticate_user_not_exists(self, auth_service):
        user = auth_service.authenticate_user("nonexistent", "12345")
        assert user is None

    # Test admin user exists
    def test_admin_user_exists(self, auth_service):
        admin = auth_service.get_user("admin")
        assert admin is not None
        assert admin["role"] == "admin"

    # Test get all users
    def test_get_all_users(self, auth_service):
        users = auth_service.get_all_users()
        assert isinstance(users, list)
        assert len(users) >= 2

    # Test password is hashed
    def test_user_password_hashed(self, auth_service):
        user = auth_service.get_user("user")
        assert user is not None
        assert user["password"].startswith("$2b$")
        assert user["password"] != "12345"

    # Test admin authentication
    def test_authenticate_admin_success(self, auth_service):
        admin = auth_service.authenticate_user("admin", "12345")
        assert admin is not None
        assert admin["username"] == "admin"
        assert admin["role"] == "admin"
