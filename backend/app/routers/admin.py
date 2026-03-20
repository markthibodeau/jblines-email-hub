"""Admin-only routes: sync status, user management, inbox configuration."""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, SyncLog
from app.auth import require_admin, get_current_user

router = APIRouter()


@router.get("/sync-status")
async def sync_status(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """View sync status for all inboxes."""
    result = await db.execute(select(SyncLog).order_by(SyncLog.inbox))
    logs = result.scalars().all()
    return [
        {
            "inbox": log.inbox,
            "status": log.status,
            "last_synced_at": log.last_synced_at,
            "emails_synced": log.emails_synced,
            "error_message": log.error_message,
        }
        for log in logs
    ]


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List all team member accounts."""
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    return [
        {
            "id": u.id, "email": u.email, "name": u.name,
            "role": u.role, "is_active": u.is_active,
            "last_login": u.last_login,
        }
        for u in users
    ]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Enable/disable a user or change their role."""
    user = await db.get(User, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    allowed_fields = {"is_active", "role", "name"}
    for field, value in payload.items():
        if field in allowed_fields:
            setattr(user, field, value)

    await db.commit()
    return {"message": "User updated", "user_id": user_id}
