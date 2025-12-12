
import pytest
from fastapi import HTTPException

from app.utils.auth import (
    create_access_token,
    hash_password,
    verify_password,
    get_user_from_db,
)


class TestAuthUtilities:

    # Test password hashing
    def test_hash_password(self):
        plain = "test_password"
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith("$2b$")

    # Test password verification with correct password
    def test_verify_password_correct(self):
        plain = "test_password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    # Test password verification with incorrect password
    def test_verify_password_incorrect(self):
        plain = "test_password"
        hashed = hash_password(plain)
        assert verify_password("wrong_password", hashed) is False

    # Test access token creation
    def test_create_access_token(self):
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    # Test access token with custom expiry
    def test_create_access_token_custom_expiry(self):
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data, expires_delta_minutes=60)
        assert isinstance(token, str)
        assert len(token) > 0

    # Test get user from db when user exists
    def test_get_user_from_db_exists(self):
        users_db = [
            {"username": "test", "password": "hash", "role": "user"},
            {"username": "admin", "password": "hash2", "role": "admin"},
        ]
        user = get_user_from_db("test", users_db)
        assert user is not None
        assert user["username"] == "test"

    # Test get user from db when user does not exist
    def test_get_user_from_db_not_exists(self):
        users_db = [{"username": "test", "password": "hash", "role": "user"}]
        user = get_user_from_db("nonexistent", users_db)
        assert user is None

    # Test get user from empty db
    def test_get_user_from_db_empty(self):
        user = get_user_from_db("test", [])
        assert user is None
