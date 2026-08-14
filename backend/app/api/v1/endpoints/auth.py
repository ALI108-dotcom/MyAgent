"""Authentication & User REST API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.config import settings
from app.core.middleware import login_rate_limiter
from app.core.security import (
    create_access_token,
    get_current_user,
    user_manager,
    verify_password,
)
from app.models.auth import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new user profile after enforcing password complexity policy.",
)
async def register(user_create: UserCreate) -> UserRead:
    """Register user."""
    return await user_manager.create_user(user_create)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login and JWT Bearer token issuance",
    description="Authenticates user credentials and issues signed JWT access token.",
)
async def login(
    login_req: LoginRequest, request: Request, response: Response
) -> TokenResponse:
    """Authenticate user login."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"login:{client_ip}:{login_req.username}"
    login_rate_limiter.check_rate_limit(rate_key)

    user = await user_manager.get_by_username(login_req.username)
    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Set HttpOnly, SameSite=Lax cookie for XSS protection
    response.set_cookie(
        key="agentai_access_token",
        value=access_token,
        httponly=True,
        max_age=expires_in,
        samesite="lax",
        secure=(settings.ENVIRONMENT == "production"),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserRead(**user.model_dump()),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout and session cookie invalidation",
    description="Clears HttpOnly authentication cookie.",
)
async def logout(response: Response) -> dict[str, str]:
    """Logout user."""
    response.delete_cookie(key="agentai_access_token")
    return {"status": "success", "message": "Successfully logged out."}


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile",
    description="Returns current authenticated user details.",
)
async def get_me(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """Get authenticated user profile."""
    return current_user
