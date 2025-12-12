from typing import Any, Dict, Optional

from ..models.enums import PeranUser
from ..utils.auth import hash_password, verify_password


class AuthService:
    """Service for managing authentication."""

    def __init__(self):
        """Initialize auth service with demo users."""
        self.users_db = [
            {
                "username": "user",
                "password": hash_password("12345"),
                "role": PeranUser.USER.value,
                "name": "User",
            },
            {
                "username": "admin",
                "password": hash_password("12345"),
                "role": PeranUser.ADMIN.value,
                "name": "Admin",
            },
        ]

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        for u in self.users_db:
            if u["username"] == username:
                return u
        return None

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password."""
        user = self.get_user(username)
        if not user:
            return None
        if not verify_password(password, user["password"]):
            return None
        return user

    def get_all_users(self):
        """Get all users (for internal use)."""
        return self.users_db
