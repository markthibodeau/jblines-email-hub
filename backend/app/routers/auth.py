"""
Auth routes: login, register (admin only), and get current user profile.
"""

import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin
)

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "staff"  # staff | admin


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


@router.post("/login", response_model=TokenOut)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/register", response_model=UserOut)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),  # Only admins can create accounts
):
    """Create a new team member account. Admin only."""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        name=payload.name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/setup")
async def initial_setup(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    One-time setup endpoint to create the first admin account.
    Disabled automatically once any user exists.
    Protected by SETUP_SECRET env var.
    """
    setup_secret = os.environ.get("SETUP_SECRET", "")
    if payload.password != setup_secret and setup_secret:
        raise HTTPException(status_code=403, detail="Invalid setup secret")

    result = await db.execute(select(User))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Setup already complete")

    user = User(
        email=payload.email.lower(),
        name=payload.name,
        role="admin",
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "Admin account created", "email": user.email}
