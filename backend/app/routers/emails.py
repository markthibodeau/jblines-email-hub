"""
Email routes — list, search, and view emails with privacy enforcement.

Privacy rules:
- Admins see everything, including raw content from private inboxes
- Staff see all emails BUT content from private inboxes is redacted
- Extracted customer/billing/schedule data is always visible to all staff
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Email, User
from app.auth import get_current_user, apply_privacy

router = APIRouter()


class EmailOut(BaseModel):
    id: str
    thread_id: str
    inbox: str
    is_private_inbox: bool
    sender: str
    sender_name: Optional[str]
    recipient: str
    subject: Optional[str]
    body_snippet: Optional[str]
    body_text: Optional[str]
    received_at: datetime
    is_read: bool
    category: Optional[str]
    ai_summary: Optional[str]
    ai_sentiment: Optional[str]
    customer_id: Optional[int]
    billing_record_id: Optional[int]
    meeting_id: Optional[int]
    is_redacted: bool = False

    class Config:
        from_attributes = True


@router.get("/", response_model=list[EmailOut])
async def list_emails(
    inbox: Optional[str] = Query(None, description="Filter by inbox email address"),
    category: Optional[str] = Query(None, description="customer | billing | schedule | general"),
    sentiment: Optional[str] = Query(None, description="positive | neutral | negative | urgent"),
    search: Optional[str] = Query(None, description="Search subject, sender, or body snippet"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List emails with optional filters. Content from private inboxes is redacted for staff."""
    query = select(Email).order_by(desc(Email.received_at))

    if inbox:
        query = query.where(Email.inbox == inbox.lower())
    if category:
        query = query.where(Email.category == category)
    if sentiment:
        query = query.where(Email.ai_sentiment == sentiment)
    if search:
        query = query.where(
            or_(
                Email.subject.ilike(f"%{search}%"),
                Email.sender.ilike(f"%{search}%"),
                Email.sender_name.ilike(f"%{search}%"),
                Email.body_snippet.ilike(f"%{search}%"),
            )
        )

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    emails = result.scalars().all()

    return [apply_privacy(_email_to_dict(e), current_user) for e in emails]


@router.get("/stats")
async def email_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard stats — total counts by category and sentiment."""
    from sqlalchemy import func

    result = await db.execute(
        select(Email.category, func.count(Email.id))
        .group_by(Email.category)
    )
    by_category = {row[0] or "unclassified": row[1] for row in result}

    result2 = await db.execute(
        select(Email.ai_sentiment, func.count(Email.id))
        .group_by(Email.ai_sentiment)
    )
    by_sentiment = {row[0] or "unknown": row[1] for row in result2}

    result3 = await db.execute(
        select(Email.inbox, func.count(Email.id))
        .group_by(Email.inbox)
        .order_by(func.count(Email.id).desc())
    )
    by_inbox = [{"inbox": row[0], "count": row[1]} for row in result3]

    total = sum(by_category.values())

    return {
        "total_emails": total,
        "by_category": by_category,
        "by_sentiment": by_sentiment,
        "by_inbox": by_inbox,
    }


@router.get("/{email_id}", response_model=EmailOut)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single email by ID. Content from private inboxes is redacted for staff."""
    email = await db.get(Email, email_id)
    if not email:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Email not found")

    return apply_privacy(_email_to_dict(email), current_user)


def _email_to_dict(email: Email) -> dict:
    return {
        "id": email.id,
        "thread_id": email.thread_id,
        "inbox": email.inbox,
        "is_private_inbox": email.is_private_inbox,
        "sender": email.sender,
        "sender_name": email.sender_name,
        "recipient": email.recipient,
        "subject": email.subject,
        "body_snippet": email.body_snippet,
        "body_text": email.body_text,
        "received_at": email.received_at,
        "is_read": email.is_read,
        "category": email.category,
        "ai_summary": email.ai_summary,
        "ai_sentiment": email.ai_sentiment,
        "customer_id": email.customer_id,
        "billing_record_id": email.billing_record_id,
        "meeting_id": email.meeting_id,
        "is_redacted": False,
    }
