"""Schedule routes — view and manage meetings extracted from emails."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Meeting, Customer, User
from app.auth import get_current_user

router = APIRouter()


class MeetingOut(BaseModel):
    id: int
    email_id: Optional[str]
    customer_id: Optional[int]
    title: Optional[str]
    description: Optional[str]
    scheduled_at: Optional[datetime]
    duration_minutes: Optional[int]
    location: Optional[str]
    status: str
    attendees: Optional[str]
    created_at: datetime
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None


@router.get("/", response_model=list[MeetingOut])
async def list_meetings(
    status: Optional[str] = Query(None, description="requested | confirmed | cancelled | completed"),
    upcoming_only: bool = Query(False, description="Only show future meetings"),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = (
        select(Meeting, Customer.name, Customer.email)
        .outerjoin(Customer, Meeting.customer_id == Customer.id)
        .order_by(asc(Meeting.scheduled_at))
    )

    if status:
        query = query.where(Meeting.status == status)
    if upcoming_only:
        query = query.where(Meeting.scheduled_at >= datetime.utcnow())
    if customer_id:
        query = query.where(Meeting.customer_id == customer_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)

    meetings = []
    for meeting, cname, cemail in result:
        d = {**meeting.__dict__}
        d.pop("_sa_instance_state", None)
        d["customer_name"] = cname
        d["customer_email"] = cemail
        meetings.append(d)

    return meetings


@router.get("/upcoming")
async def upcoming_meetings(
    days: int = Query(7, description="Number of days ahead to look"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Quick view: meetings in the next N days."""
    from datetime import timedelta

    now = datetime.utcnow()
    end = now + timedelta(days=days)

    result = await db.execute(
        select(Meeting, Customer.name, Customer.email)
        .outerjoin(Customer, Meeting.customer_id == Customer.id)
        .where(Meeting.scheduled_at.between(now, end))
        .where(Meeting.status.in_(["requested", "confirmed"]))
        .order_by(asc(Meeting.scheduled_at))
    )

    meetings = []
    for meeting, cname, cemail in result:
        d = {**meeting.__dict__}
        d.pop("_sa_instance_state", None)
        d["customer_name"] = cname
        d["customer_email"] = cemail
        meetings.append(d)

    return meetings


@router.patch("/{meeting_id}", response_model=MeetingOut)
async def update_meeting(
    meeting_id: int,
    payload: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Confirm, cancel, or update a meeting."""
    meeting = await db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(meeting, field, value)

    await db.commit()
    await db.refresh(meeting)

    customer = await db.get(Customer, meeting.customer_id) if meeting.customer_id else None
    d = {**meeting.__dict__}
    d.pop("_sa_instance_state", None)
    d["customer_name"] = customer.name if customer else None
    d["customer_email"] = customer.email if customer else None
    return d
