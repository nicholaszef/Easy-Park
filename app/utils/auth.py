"""Authentication and authorization utilities."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from ..models.enums import PeranUser

# Configuration
SECRET_KEY = "your-secret-key-change-in-production-min-32-chars-long"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def hash_password(plain: str) -> str:
    """Hash a plain text password."""
    password_bytes = plain.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    data: dict, expires_delta_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_from_db(username: str, users_db: list) -> Optional[Dict[str, Any]]:
    """Get user from database by username."""
    for u in users_db:
        if u["username"] == username:
            return u
    return None


def get_current_user(
    token: str = Depends(oauth2_scheme), users_db: list = None
) -> Dict[str, Any]:
    """Get current authenticated user from token."""
    if users_db is None:
        users_db = []
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kadaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_from_db(username, users_db)
    if user is None:
        raise credentials_exception
    user_copy = user.copy()
    user_copy["role"] = role
    return user_copy


def require_admin(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """Require admin role for the current user."""
    if current_user.get("role") != PeranUser.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Akses admin diperlukan"
        )
    return current_user
