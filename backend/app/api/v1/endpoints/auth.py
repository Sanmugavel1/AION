"""
AION API â€” Authentication
JWT + OAuth2 + RBAC
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession
from app.core.exceptions import AuthenticationError
from app.core.security import (
    UserRole,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    org_name: str = Field(min_length=2, max_length=255)
    industry: str = Field(default="technology", max_length=100)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: DbSession):
    """Register a new organization and admin user."""
    # Check email uniqueness
    stmt = select(User).where(User.email == request.email)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create organization
    org = Organization(
        name=request.org_name,
        slug=request.org_name.lower().replace(" ", "-"),
    )
    db.add(org)
    await db.flush()

    # Create admin user
    user = User(
        org_id=org.id,
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=UserRole.ORG_ADMIN.value,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        subject=str(user.id),
        org_id=str(org.id),
        role=UserRole.ORG_ADMIN,
        additional_claims={"email": user.email},
    )
    refresh_token = create_refresh_token(str(user.id), str(org.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email/username and password."""
    stmt = select(User).where(
        (User.email == form_data.username) | (User.username == form_data.username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")

    role = UserRole(user.role)
    access_token = create_access_token(
        subject=str(user.id),
        org_id=str(user.org_id),
        role=role,
        additional_claims={"email": user.email},
    )
    refresh_token = create_refresh_token(str(user.id), str(user.org_id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: DbSession):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload["sub"]
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    role = UserRole(user.role)
    new_access = create_access_token(
        subject=str(user.id),
        org_id=str(user.org_id),
        role=role,
        additional_claims={"email": user.email},
    )
    new_refresh = create_refresh_token(str(user.id), str(user.org_id))
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me")
async def get_current_user_info(current_user: AuthUser):
    """Get current authenticated user info."""
    return {
        "user_id": current_user.user_id,
        "org_id": current_user.org_id,
        "email": current_user.email,
        "role": current_user.role.value,
        "permissions": current_user.permissions,
    }
