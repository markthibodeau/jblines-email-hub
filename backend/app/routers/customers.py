"""
Customer routes — view and manage customer profiles built from email history.
Visible to all authenticated staff (no privacy restrictions on extracted data).
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer, Email, BillingRecord, Meeting, User
from app.auth import get_current_user

router = APIRouter()


class CustomerOut(BaseModel):
    id: int
    email: str
    name: Optional[str]
    company: Optional[str]
    phone: Optional[str]
    first_contact: Optional[datetime]
    last_contact: Optional[datetime]
    email_count: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


@router.get("/", response_model=list[CustomerOut])
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List all customers, optionally filtered by search term."""
    query = select(Customer).order_by(desc(Customer.last_contact))

    if search:
        query = query.where(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Customer.company.ilike(f"%{search}%"),
            )
        )

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/timeline")
async def get_customer_timeline(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full activity timeline for a customer — emails, billing, meetings.
    Email content from private inboxes is redacted for staff.
    """
    from app.auth import apply_privacy

    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Emails
    email_result = await db.execute(
        select(Email)
        .where(Email.customer_id == customer_id)
        .order_by(desc(Email.received_at))
        .limit(100)
    )
    emails = [
        apply_privacy({
            "id": e.id, "thread_id": e.thread_id, "inbox": e.inbox,
            "is_private_inbox": e.is_private_inbox, "sender": e.sender,
            "sender_name": e.sender_name, "recipient": e.recipient,
            "subject": e.subject, "body_snippet": e.body_snippet,
            "body_text": None,  # Never send full body in timeline
            "received_at": e.received_at, "is_read": e.is_read,
            "category": e.category, "ai_summary": e.ai_summary,
            "ai_sentiment": e.ai_sentiment, "customer_id": e.customer_id,
            "billing_record_id": e.billing_record_id, "meeting_id": e.meeting_id,
            "is_redacted": False,
        }, current_user)
        for e in email_result.scalars().all()
    ]

    # Billing records
    billing_result = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.customer_id == customer_id)
        .order_by(desc(BillingRecord.created_at))
    )
    billing = [
        {
            "id": b.id, "billing_type": b.billing_type, "amount": b.amount,
            "currency": b.currency, "invoice_number": b.invoice_number,
            "due_date": b.due_date, "paid_date": b.paid_date,
            "status": b.status, "description": b.description,
        }
        for b in billing_result.scalars().all()
    ]

    # Meetings
    meeting_result = await db.execute(
        select(Meeting)
        .where(Meeting.customer_id == customer_id)
        .order_by(desc(Meeting.scheduled_at))
    )
    meetings = [
        {
            "id": m.id, "title": m.title, "scheduled_at": m.scheduled_at,
            "duration_minutes": m.duration_minutes, "location": m.location,
            "status": m.status, "attendees": m.attendees,
        }
        for m in meeting_result.scalars().all()
    ]

    return {
        "customer": customer,
        "emails": emails,
        "billing": billing,
        "meetings": meetings,
    }


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Manually update a customer's name, company, phone, or notes."""
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    return customer
