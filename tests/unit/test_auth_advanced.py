import pytest
from fastapi import HTTPException
from jose import jwt

from app.utils.auth import (
    get_current_user,
    require_admin,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM,
)


class TestGetCurrentUser:

    # Test get current user with valid token
    def test_get_current_user_valid_token(self):
        users_db = [
            {"username": "testuser", "password": "hash", "role": "user", "name": "Test"}
        ]
        token_data = {"sub": "testuser", "role": "user"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        user = get_current_user(token, users_db)
        assert user["username"] == "testuser"
        assert user["role"] == "user"

    # Test get current user with invalid token
    def test_get_current_user_invalid_token(self):
        users_db = [{"username": "testuser", "password": "hash", "role": "user"}]
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc:
            get_current_user(invalid_token, users_db)
        assert exc.value.status_code == 401

    # Test get current user with missing username in token
    def test_get_current_user_missing_username(self):
        users_db = [{"username": "testuser", "password": "hash", "role": "user"}]
        token_data = {"role": "user"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc:
            get_current_user(token, users_db)
        assert exc.value.status_code == 401

    # Test get current user with missing role in token
    def test_get_current_user_missing_role(self):
        users_db = [{"username": "testuser", "password": "hash", "role": "user"}]
        token_data = {"sub": "testuser"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc:
            get_current_user(token, users_db)
        assert exc.value.status_code == 401

    # Test get current user not in database
    def test_get_current_user_not_in_db(self):
        users_db = [{"username": "otheruser", "password": "hash", "role": "user"}]
        token_data = {"sub": "testuser", "role": "user"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc:
            get_current_user(token, users_db)
        assert exc.value.status_code == 401

    # Test get current user with empty database
    def test_get_current_user_empty_db(self):
        users_db = []
        token_data = {"sub": "testuser", "role": "user"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc:
            get_current_user(token, users_db)
        assert exc.value.status_code == 401


class TestRequireAdmin:

    # Test require admin success
    def test_require_admin_success(self):
        admin_user = {"username": "admin", "role": "admin", "name": "Admin"}
        result = require_admin(admin_user)
        assert result == admin_user

    # Test require admin forbidden for regular user
    def test_require_admin_forbidden(self):
        regular_user = {"username": "user", "role": "user", "name": "User"}
        with pytest.raises(HTTPException) as exc:
            require_admin(regular_user)
        assert exc.value.status_code == 403
        assert "Admin" in exc.value.detail or "admin" in exc.value.detail
