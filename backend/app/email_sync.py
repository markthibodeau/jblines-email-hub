"""
Email sync engine — runs every 15 minutes via APScheduler.

Flow per inbox:
  1. Check SyncLog for last sync position (Gmail history ID)
  2. Fetch new messages since last sync (or pull SYNC_DAYS_BACK days on first run)
  3. Parse + store each email in the database
  4. Run Claude classification on unclassified emails
  5. Upsert Customer, BillingRecord, and Meeting records from classification results
  6. Update SyncLog with new history ID and timestamp
"""

import os
import logging
from datetime import datetime, timedelta, timezone

from googleapiclient.errors import HttpError
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models import Email, Customer, BillingRecord, Meeting, SyncLog
from app.gmail_client import get_company_inboxes, get_gmail_service, fetch_messages, fetch_message_detail, parse_message
from app.classifier import classify_email
from app.auth import get_private_inboxes

logger = logging.getLogger(__name__)

SYNC_DAYS_BACK = int(os.environ.get("SYNC_DAYS_BACK", "180"))  # Default: 6 months of history
CLASSIFY_BATCH_SIZE = 20  # Emails to classify per sync cycle (controls API cost)


async def sync_all_inboxes():
    """Main entry point — syncs every configured inbox."""
    inboxes = get_company_inboxes()
    if not inboxes:
        logger.warning("No COMPANY_INBOXES configured. Skipping sync.")
        return

    logger.info(f"Starting sync for {len(inboxes)} inbox(es): {inboxes}")
    for inbox in inboxes:
        try:
            await sync_inbox(inbox)
        except Exception as e:
            logger.error(f"Sync failed for {inbox}: {e}", exc_info=True)
            await _update_sync_log(inbox, status="error", error=str(e))


async def sync_inbox(inbox: str):
    """Sync a single inbox: fetch new emails, classify, and update records."""
    private_inboxes = get_private_inboxes()
    is_private = inbox.lower() in private_inboxes

    async with AsyncSessionLocal() as db:
        # Check last sync position
        result = await db.execute(select(SyncLog).where(SyncLog.inbox == inbox))
        sync_log = result.scalar_one_or_none()

        await _update_sync_log(inbox, status="syncing")

        # Determine date cutoff for first-time sync
        if sync_log and sync_log.last_synced_at:
            # Incremental: only fetch emails since last sync
            cutoff_date = sync_log.last_synced_at
            logger.info(f"{inbox}: incremental sync since {cutoff_date}")
        else:
            # First time: fetch SYNC_DAYS_BACK days of history
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=SYNC_DAYS_BACK)
            logger.info(f"{inbox}: first sync, fetching last {SYNC_DAYS_BACK} days")

        # Fetch and store emails
        new_count = await _fetch_and_store(db, inbox, cutoff_date, is_private)

        # Classify unprocessed emails (batched to control cost)
        classified = await _classify_pending(db, inbox)

        # Update sync log
        await _update_sync_log(inbox, status="idle", emails_synced=new_count)
        logger.info(f"{inbox}: synced {new_count} new, classified {classified}")


async def _fetch_and_store(db, inbox: str, since: datetime, is_private: bool) -> int:
    """Fetch messages from Gmail API and insert new ones into the database."""
    service = get_gmail_service(inbox)

    # Build Gmail query: emails newer than cutoff
    after_timestamp = int(since.timestamp())
    query = f"after:{after_timestamp}"

    new_count = 0
    page_token = None

    while True:
        kwargs = {
            "userId": "me",
            "maxResults": 500,
            "q": query,
        }
        if page_token:
            kwargs["pageToken"] = page_token

        try:
            response = service.users().messages().list(**kwargs).execute()
        except HttpError as e:
            logger.error(f"Gmail API error for {inbox}: {e}")
            break

        messages = response.get("messages", [])
        if not messages:
            break

        for msg_ref in messages:
            msg_id = msg_ref["id"]

            # Skip if already stored
            existing = await db.get(Email, msg_id)
            if existing:
                continue

            try:
                raw = service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                parsed = parse_message(raw, inbox)
                parsed["is_private_inbox"] = is_private

                email = Email(**parsed)
                db.add(email)
                new_count += 1
            except HttpError as e:
                logger.warning(f"Could not fetch message {msg_id} from {inbox}: {e}")
                continue

        await db.commit()

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return new_count


async def _classify_pending(db, inbox: str) -> int:
    """Classify emails that haven't been processed by Claude yet."""
    result = await db.execute(
        select(Email)
        .where(Email.inbox == inbox, Email.classified_at == None)
        .limit(CLASSIFY_BATCH_SIZE)
    )
    emails = result.scalars().all()

    classified_count = 0
    for email in emails:
        email_dict = {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "sender_name": email.sender_name,
            "recipient": email.recipient,
            "inbox": email.inbox,
            "body_text": email.body_text,
            "body_snippet": email.body_snippet,
        }

        classification = await classify_email(email_dict)

        # Update email with classification
        email.category = classification.get("category", "general")
        email.ai_summary = classification.get("summary")
        email.ai_sentiment = classification.get("sentiment", "neutral")
        email.classified_at = datetime.utcnow()

        # Upsert customer record
        customer = await _upsert_customer(db, email, classification)
        if customer:
            email.customer_id = customer.id

        # Create billing record if detected
        if classification.get("billing_type"):
            billing = await _create_billing_record(db, email, classification, customer)
            if billing:
                email.billing_record_id = billing.id

        # Create meeting record if detected
        if classification.get("meeting_date") or classification.get("meeting_title"):
            meeting = await _create_meeting_record(db, email, classification, customer)
            if meeting:
                email.meeting_id = meeting.id

        classified_count += 1

    await db.commit()
    return classified_count


async def _upsert_customer(db, email: Email, classification: dict):
    """Find or create a customer record based on the email sender."""
    # Don't create customers for internal company emails
    company_inboxes = set(get_company_inboxes())
    if email.sender.lower() in company_inboxes:
        return None

    result = await db.execute(
        select(Customer).where(Customer.email == email.sender.lower())
    )
    customer = result.scalar_one_or_none()

    if customer:
        # Update last contact and email count
        customer.last_contact = email.received_at
        customer.email_count += 1
        if classification.get("customer_name") and not customer.name:
            customer.name = classification["customer_name"]
        if classification.get("customer_company") and not customer.company:
            customer.company = classification["customer_company"]
        if classification.get("customer_phone") and not customer.phone:
            customer.phone = classification["customer_phone"]
    else:
        customer = Customer(
            email=email.sender.lower(),
            name=classification.get("customer_name") or email.sender_name,
            company=classification.get("customer_company"),
            phone=classification.get("customer_phone"),
            first_contact=email.received_at,
            last_contact=email.received_at,
            email_count=1,
        )
        db.add(customer)
        await db.flush()  # Get the ID

    return customer


async def _create_billing_record(db, email: Email, classification: dict, customer) -> BillingRecord:
    """Create a billing record from classified email data."""
    due_date = None
    if classification.get("due_date"):
        try:
            due_date = datetime.strptime(classification["due_date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    billing = BillingRecord(
        email_id=email.id,
        customer_id=customer.id if customer else None,
        billing_type=classification.get("billing_type", "invoice"),
        amount=classification.get("billing_amount"),
        currency=classification.get("billing_currency", "USD"),
        invoice_number=classification.get("invoice_number"),
        due_date=due_date,
        status="pending",
        description=classification.get("summary"),
    )
    db.add(billing)
    await db.flush()
    return billing


async def _create_meeting_record(db, email: Email, classification: dict, customer) -> Meeting:
    """Create a meeting record from classified email data."""
    scheduled_at = None
    if classification.get("meeting_date"):
        try:
            date_str = classification["meeting_date"]
            time_str = classification.get("meeting_time", "09:00")
            scheduled_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass

    meeting = Meeting(
        email_id=email.id,
        customer_id=customer.id if customer else None,
        title=classification.get("meeting_title") or email.subject,
        description=classification.get("summary"),
        scheduled_at=scheduled_at,
        duration_minutes=classification.get("meeting_duration_minutes"),
        location=classification.get("meeting_location"),
        status="requested",
        attendees=f"{email.sender},{email.inbox}",
    )
    db.add(meeting)
    await db.flush()
    return meeting


async def _update_sync_log(inbox: str, status: str, emails_synced: int = 0, error: str = None):
    """Update or create a SyncLog entry for an inbox."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SyncLog).where(SyncLog.inbox == inbox))
        log = result.scalar_one_or_none()

        if log:
            log.status = status
            log.error_message = error
            if status == "idle":
                log.last_synced_at = datetime.utcnow()
                log.emails_synced = (log.emails_synced or 0) + emails_synced
        else:
            log = SyncLog(
                inbox=inbox,
                status=status,
                error_message=error,
                emails_synced=emails_synced,
                last_synced_at=datetime.utcnow() if status == "idle" else None,
            )
            db.add(log)

        await db.commit()
