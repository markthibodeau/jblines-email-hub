"""
Chat route — ask Claude questions about your company's email data.

Staff ask questions in plain English. Claude searches the database for
relevant emails, customers, billing, and meetings, then answers.

Privacy: Claude will not include content from private inboxes when responding
to staff users. Admins get the full picture.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Email, Customer, BillingRecord, Meeting, User
from app.auth import get_current_user
from app.classifier import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    context_filter: Optional[str] = None  # Optional: "billing", "customers", "schedule"


class ChatResponse(BaseModel):
    answer: str
    emails_used: int


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Answer a natural language question using email data as context.

    Examples:
    - "What's the status of the invoice from Acme Corp?"
    - "Who has meetings scheduled this week?"
    - "Show me all overdue payments"
    - "What did John Smith email us about last month?"
    """
    question = request.question.strip()
    is_admin = current_user.role == "admin"

    # --- Pull relevant emails for context ---
    # Strategy: keyword search on question terms + filter by context
    keywords = _extract_keywords(question)

    email_query = (
        select(Email)
        .order_by(desc(Email.received_at))
        .limit(30)
    )

    # Filter out private inbox content for staff users
    if not is_admin:
        email_query = email_query.where(Email.is_private_inbox == False)

    # Filter by context if specified
    if request.context_filter:
        email_query = email_query.where(Email.category == request.context_filter)

    # Keyword search
    if keywords:
        conditions = [
            or_(
                Email.subject.ilike(f"%{kw}%"),
                Email.sender.ilike(f"%{kw}%"),
                Email.sender_name.ilike(f"%{kw}%"),
                Email.body_snippet.ilike(f"%{kw}%"),
                Email.ai_summary.ilike(f"%{kw}%"),
            )
            for kw in keywords
        ]
        from sqlalchemy import or_ as sql_or
        email_query = email_query.where(sql_or(*conditions))

    result = await db.execute(email_query)
    emails = result.scalars().all()

    # Convert to dicts for Claude
    email_dicts = [
        {
            "id": e.id,
            "inbox": e.inbox,
            "sender": e.sender,
            "sender_name": e.sender_name,
            "subject": e.subject,
            "received_at": str(e.received_at),
            "category": e.category,
            "ai_summary": e.ai_summary,
            "ai_sentiment": e.ai_sentiment,
            "body_snippet": e.body_snippet,
        }
        for e in emails
    ]

    # If no emails found, supplement with billing / schedule summaries
    if len(email_dicts) < 5:
        supplement = await _get_supplemental_context(db, question, is_admin)
        email_dicts.extend(supplement)

    answer = await answer_question(question, email_dicts)

    return {"answer": answer, "emails_used": len(email_dicts)}


async def _get_supplemental_context(db, question: str, is_admin: bool) -> list[dict]:
    """Add billing/meeting summaries when email search returns few results."""
    extras = []

    # Recent billing records
    billing_result = await db.execute(
        select(BillingRecord).order_by(desc(BillingRecord.created_at)).limit(10)
    )
    for b in billing_result.scalars().all():
        extras.append({
            "id": f"billing_{b.id}",
            "inbox": "billing",
            "sender": "",
            "sender_name": "",
            "subject": f"Billing: {b.billing_type} - ${b.amount} - {b.status}",
            "received_at": str(b.created_at),
            "category": "billing",
            "ai_summary": b.description,
            "ai_sentiment": "neutral",
            "body_snippet": f"Invoice #{b.invoice_number} | Amount: ${b.amount} {b.currency} | Status: {b.status} | Due: {b.due_date}",
        })

    # Upcoming meetings
    from datetime import datetime
    meeting_result = await db.execute(
        select(Meeting)
        .where(Meeting.scheduled_at >= datetime.utcnow())
        .order_by(Meeting.scheduled_at)
        .limit(10)
    )
    for m in meeting_result.scalars().all():
        extras.append({
            "id": f"meeting_{m.id}",
            "inbox": "schedule",
            "sender": "",
            "sender_name": "",
            "subject": f"Meeting: {m.title}",
            "received_at": str(m.created_at),
            "category": "schedule",
            "ai_summary": m.description,
            "ai_sentiment": "neutral",
            "body_snippet": f"Scheduled: {m.scheduled_at} | Location: {m.location} | Status: {m.status} | Attendees: {m.attendees}",
        })

    return extras


def _extract_keywords(question: str) -> list[str]:
    """Extract meaningful search keywords from the question."""
    import re
    # Remove common stop words
    stop_words = {
        "what", "who", "when", "where", "how", "why", "is", "are", "was",
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "about", "show", "me", "all", "any",
        "can", "did", "do", "does", "has", "have", "had", "been", "be",
        "get", "give", "tell", "find", "list", "this", "that", "these",
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
    keywords = [w for w in words if w not in stop_words]
    return keywords[:5]  # Top 5 keywords
