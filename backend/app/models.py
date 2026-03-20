"""
Database models for the Email Hub.
Each table maps to a core concept: Email, Customer, BillingRecord, Meeting, User.

Privacy model:
- PRIVATE_INBOXES (env var) lists inboxes whose raw email content is admin-only.
- Extracted data (customers, billing, meetings) from those inboxes is visible to all staff.
- Only users with role='admin' can read raw email bodies/subjects from private inboxes.
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    """Team member who can log in to the dashboard."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="staff")  # admin | staff
    # 'admin' role = full access including private inbox raw content
    # 'staff' role = access to extracted data only for private inboxes
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Email(Base):
    """Raw email record synced from Gmail."""
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # Gmail message ID
    thread_id: Mapped[str] = mapped_column(String(32), index=True)
    inbox: Mapped[str] = mapped_column(String(255), index=True)
    is_private_inbox: Mapped[bool] = mapped_column(Boolean, default=False)
    # ↑ True for inboxes listed in PRIVATE_INBOXES env var.
    # When True, only admins can see subject/body/sender of this email.

    sender: Mapped[str] = mapped_column(String(255), index=True)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=True)
    recipient: Mapped[str] = mapped_column(String(512))
    subject: Mapped[str] = mapped_column(Text, nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=True)
    body_snippet: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI classification
    category: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)
    ai_sentiment: Mapped[str] = mapped_column(String(20), nullable=True)
    classified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Links to structured records (always accessible regardless of privacy)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    billing_record_id: Mapped[int] = mapped_column(ForeignKey("billing_records.id"), nullable=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="emails")


class Customer(Base):
    """A customer profile built from email history. Visible to all staff."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    first_contact: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_contact: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    emails: Mapped[list["Email"]] = relationship("Email", back_populates="customer")
    billing_records: Mapped[list["BillingRecord"]] = relationship("BillingRecord", back_populates="customer")
    meetings: Mapped[list["Meeting"]] = relationship("Meeting", back_populates="customer")


class BillingRecord(Base):
    """A billing event extracted from email. Visible to all staff."""
    __tablename__ = "billing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[str] = mapped_column(String(32), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    billing_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    paid_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="billing_records")


class Meeting(Base):
    """A meeting or appointment extracted from email. Visible to all staff."""
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[str] = mapped_column(String(32), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="requested")
    attendees: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="meetings")


class SyncLog(Base):
    """Tracks last sync time per inbox for incremental sync."""
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inbox: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_history_id: Mapped[str] = mapped_column(String(50), nullable=True)
    emails_synced: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="idle")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
