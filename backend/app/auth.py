"""
Authentication and privacy enforcement.

- JWT-based login (email + password)
- Role checking: admin vs staff
- Privacy helpers: redact email content from private inboxes for non-admins
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that blocks non-admins."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Privacy helpers ───────────────────────────────────────────────────────────

def get_private_inboxes() -> set[str]:
    """
    Returns the set of inbox emails that are marked as private.
    Set PRIVATE_INBOXES=mark@jblines.com,ben@jblines.com in your .env
    """
    raw = os.environ.get("PRIVATE_INBOXES", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def redact_email_for_staff(email_dict: dict) -> dict:
    """
    For non-admin users viewing an email from a private inbox,
    replace sensitive content with a redaction notice.
    The customer/billing/schedule extracted data is still available
    via their own endpoints — only the raw email thread is hidden.
    """
    return {
        **email_dict,
        "subject": "[Private — admin access required]",
        "body_text": None,
        "body_snippet": "[Content hidden — this email is from a private inbox]",
        "sender": "private",
        "sender_name": "Private Inbox",
        "recipient": "private",
        "is_redacted": True,
    }


def apply_privacy(email_dict: dict, user: User) -> dict:
    """
    Apply redaction to an email dict if the user is staff and the inbox is private.
    Admins always see everything.
    """
    if user.role == "admin":
        return {**email_dict, "is_redacted": False}
    if email_dict.get("is_private_inbox"):
        return redact_email_for_staff(email_dict)
    return {**email_dict, "is_redacted": False}
