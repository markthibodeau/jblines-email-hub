"""Billing routes — view invoices, payments, quotes, and overdue items."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import BillingRecord, Customer, User
from app.auth import get_current_user

router = APIRouter()


class BillingOut(BaseModel):
    id: int
    email_id: Optional[str]
    customer_id: Optional[int]
    billing_type: str
    amount: Optional[float]
    currency: str
    invoice_number: Optional[str]
    due_date: Optional[datetime]
    paid_date: Optional[datetime]
    status: str
    description: Optional[str]
    created_at: datetime
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True


class BillingUpdate(BaseModel):
    status: Optional[str] = None
    paid_date: Optional[datetime] = None
    amount: Optional[float] = None
    invoice_number: Optional[str] = None
    due_date: Optional[datetime] = None


@router.get("/", response_model=list[BillingOut])
async def list_billing(
    status: Optional[str] = Query(None, description="pending | paid | overdue | cancelled"),
    billing_type: Optional[str] = Query(None, description="invoice | payment | quote | overdue | refund"),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = (
        select(BillingRecord, Customer.name, Customer.email)
        .outerjoin(Customer, BillingRecord.customer_id == Customer.id)
        .order_by(desc(BillingRecord.created_at))
    )

    if status:
        query = query.where(BillingRecord.status == status)
    if billing_type:
        query = query.where(BillingRecord.billing_type == billing_type)
    if customer_id:
        query = query.where(BillingRecord.customer_id == customer_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)

    records = []
    for billing, cname, cemail in result:
        d = {**billing.__dict__}
        d.pop("_sa_instance_state", None)
        d["customer_name"] = cname
        d["customer_email"] = cemail
        records.append(d)

    return records


@router.get("/summary")
async def billing_summary(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Financial summary: total invoiced, collected, pending, overdue."""
    from sqlalchemy import func

    result = await db.execute(
        select(BillingRecord.status, func.sum(BillingRecord.amount), func.count(BillingRecord.id))
        .group_by(BillingRecord.status)
    )

    summary = {}
    for status, total, count in result:
        summary[status or "unknown"] = {"total": round(total or 0, 2), "count": count}

    return summary


@router.get("/{billing_id}", response_model=BillingOut)
async def get_billing_record(
    billing_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BillingRecord, Customer.name, Customer.email)
        .outerjoin(Customer, BillingRecord.customer_id == Customer.id)
        .where(BillingRecord.id == billing_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Billing record not found")

    billing, cname, cemail = row
    d = {**billing.__dict__}
    d.pop("_sa_instance_state", None)
    d["customer_name"] = cname
    d["customer_email"] = cemail
    return d


@router.patch("/{billing_id}", response_model=BillingOut)
async def update_billing_record(
    billing_id: int,
    payload: BillingUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Mark an invoice as paid, update amounts, etc."""
    billing = await db.get(BillingRecord, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(billing, field, value)

    await db.commit()
    await db.refresh(billing)

    # Fetch customer info for response
    customer = await db.get(Customer, billing.customer_id) if billing.customer_id else None
    d = {**billing.__dict__}
    d.pop("_sa_instance_state", None)
    d["customer_name"] = customer.name if customer else None
    d["customer_email"] = customer.email if customer else None
    return d
