"""Security, Cryptography, JWT Authentication, and RBAC Authorization module."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.database import db_manager
from app.models.auth import User, UserCreate, UserRead, UserRole

# HTTP Bearer scheme for token extraction
security_scheme = HTTPBearer(auto_error=False)


def validate_password_complexity(password: str) -> None:
    """Validate password complexity requirements to prevent weak passwords."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password policy error: Password must be at least 8 characters long.",
        )
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password policy error: Password must contain at least one uppercase letter.",
        )
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password policy error: Password must contain at least one lowercase letter.",
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password policy error: Password must contain at least one digit.",
        )
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password policy error: Password must contain at least one special character.",
        )


def hash_password(password: str) -> str:
    """Hash plaintext password securely using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pw_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bool(bcrypt.checkpw(pw_bytes, hash_bytes))
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Encode user claims into a signed JWT access token with issuer and audience."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })

    encoded: str = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate signed JWT access token enforcing claims verification."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: JWT token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except jwt.InvalidIssuerError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: JWT token issuer is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except jwt.InvalidAudienceError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: JWT token audience is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except jwt.PyJWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Invalid JWT token signature or format.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


class UserManager:
    """Manages User account persistence in MongoDB with in-memory fallback."""

    def __init__(self) -> None:
        self._in_memory_users: dict[str, User] = {}
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Seed default test accounts strictly in development or testing mode."""
        if settings.ENVIRONMENT not in ("development", "testing"):
            return

        now = datetime.now(timezone.utc).isoformat()
        admin_user = User(
            user_id="user-admin-001",
            username="admin",
            email="admin@agentai.dev",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        standard_user = User(
            user_id="user-standard-002",
            username="user",
            email="user@agentai.dev",
            password_hash=hash_password("UserPass123!"),
            role="user",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._in_memory_users["admin"] = admin_user
        self._in_memory_users["user"] = standard_user

    async def create_user(
        self, user_create: UserCreate, role: UserRole = "user"
    ) -> UserRead:
        """Create and store new User after validating password complexity."""
        validate_password_complexity(user_create.password)

        existing = await self.get_by_username(user_create.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_create.username}' is already taken.",
            )

        now = datetime.now(timezone.utc).isoformat()
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=user_id,
            username=user_create.username,
            email=user_create.email,
            password_hash=hash_password(user_create.password),
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        if db_manager.db is not None:
            try:
                await db_manager.db["users"].insert_one(user.model_dump())
            except Exception:
                self._in_memory_users[user.username] = user
        else:
            self._in_memory_users[user.username] = user

        return UserRead(**user.model_dump())

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve user by username."""
        if db_manager.db is not None:
            try:
                doc = await db_manager.db["users"].find_one({"username": username})
                if doc:
                    doc.pop("_id", None)
                    return User(**doc)
            except Exception:
                pass

        return self._in_memory_users.get(username)

    async def get_by_id(self, user_id: str) -> User | None:
        """Retrieve user by user_id."""
        if db_manager.db is not None:
            try:
                doc = await db_manager.db["users"].find_one({"user_id": user_id})
                if doc:
                    doc.pop("_id", None)
                    return User(**doc)
            except Exception:
                pass

        for u in self._in_memory_users.values():
            if u.user_id == user_id:
                return u
        return None


user_manager = UserManager()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> UserRead:
    """FastAPI dependency validating JWT from Bearer header or HttpOnly cookie."""
    token: str | None = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request.cookies.get("agentai_access_token"):
        token = request.cookies.get("agentai_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing Bearer authorization header or cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Invalid token subject claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_manager.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: User account is inactive.",
        )

    return UserRead(**user.model_dump())


async def require_admin(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """FastAPI dependency enforcing ADMIN role authorization."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Administrative privileges (ADMIN role) required.",
        )
    return current_user
