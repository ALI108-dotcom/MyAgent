"""Pydantic schemas for User authentication, JWT tokens, and RBAC authorization."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["user", "admin"]


class User(BaseModel):
    """User database model."""

    user_id: str = Field(..., description="Unique user string identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    password_hash: str = Field(..., description="Bcrypt hashed password")
    role: UserRole = Field(default="user", description="RBAC Role (user or admin)")
    is_active: bool = Field(default=True, description="Active status flag")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 update timestamp")


class UserRead(BaseModel):
    """Public user profile model (excludes password_hash)."""

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: UserRole = Field(..., description="RBAC Role")
    is_active: bool = Field(..., description="Active status flag")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class UserCreate(BaseModel):
    """Payload schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=100, description="Plaintext password")
    role: UserRole = Field(default="user", description="Optional initial role assignment")


class LoginRequest(BaseModel):
    """Payload schema for authentication login."""

    username: str = Field(..., min_length=1, description="Username or Email")
    password: str = Field(..., min_length=1, description="Plaintext password")


class TokenResponse(BaseModel):
    """JWT Token response schema."""

    access_token: str = Field(..., description="JWT Bearer token string")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Validity period in seconds")
    user: UserRead = Field(..., description="Authenticated user profile")
