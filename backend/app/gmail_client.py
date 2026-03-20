"""
Gmail API client using a Google Service Account with domain-wide delegation.

This allows one service account to read all company inboxes without
individual user logins. Setup instructions are in SETUP.md.
"""

import os
import base64
import json
import logging
from datetime import datetime
from email import message_from_bytes
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail OAuth scopes — read-only is sufficient for syncing
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # Needed to mark emails as read
]


def get_gmail_service(user_email: str):
    """
    Build an authenticated Gmail API service for the given user email.
    Uses domain-wide delegation from the service account JSON.
    """
    # The service account key can be provided as a file path OR as a JSON string
    service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
    elif service_account_file:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
    else:
        raise ValueError(
            "No Google service account configured. "
            "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE in your environment."
        )

    # Impersonate the target user (domain-wide delegation)
    delegated_credentials = credentials.with_subject(user_email)
    service = build("gmail", "v1", credentials=delegated_credentials)
    return service


def fetch_messages(user_email: str, max_results: int = 100, page_token: Optional[str] = None) -> dict:
    """
    Fetch a list of message IDs from a user's inbox.
    Returns the raw API response (includes nextPageToken if more pages exist).
    """
    service = get_gmail_service(user_email)
    kwargs = {
        "userId": "me",
        "maxResults": max_results,
        "includeSpamTrash": False,
    }
    if page_token:
        kwargs["pageToken"] = page_token
    return service.users().messages().list(**kwargs).execute()


def fetch_message_detail(user_email: str, message_id: str) -> dict:
    """Fetch the full detail of a single message by ID."""
    service = get_gmail_service(user_email)
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()


def parse_message(raw_message: dict, inbox: str) -> dict:
    """
    Parse a raw Gmail API message into a clean dictionary
    ready to be stored in the database.
    """
    headers = {h["name"].lower(): h["value"] for h in raw_message.get("payload", {}).get("headers", [])}

    # Extract timestamp
    timestamp_ms = int(raw_message.get("internalDate", 0))
    received_at = datetime.utcfromtimestamp(timestamp_ms / 1000)

    # Extract body text
    body_text = _extract_body(raw_message.get("payload", {}))

    # Parse sender
    sender_raw = headers.get("from", "")
    sender_name, sender_email = _parse_address(sender_raw)

    return {
        "id": raw_message["id"],
        "thread_id": raw_message.get("threadId", ""),
        "inbox": inbox,
        "sender": sender_email,
        "sender_name": sender_name,
        "recipient": headers.get("to", ""),
        "subject": headers.get("subject", "(no subject)"),
        "body_text": body_text[:10000] if body_text else None,  # Truncate very long bodies
        "body_snippet": raw_message.get("snippet", "")[:500],
        "received_at": received_at,
        "is_read": "UNREAD" not in raw_message.get("labelIds", []),
    }


def _extract_body(payload: dict) -> Optional[str]:
    """Recursively extract plain text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    if mime_type == "text/html":
        # Fallback: return HTML if no plain text found
        data = payload.get("body", {}).get("data", "")
        if data:
            raw_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            # Very basic HTML strip — good enough for AI classification
            import re
            return re.sub(r"<[^>]+>", " ", raw_html)

    # Recurse into multipart
    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return None


def _parse_address(address_str: str) -> tuple[str, str]:
    """Parse 'Name <email@domain.com>' into (name, email)."""
    import re
    match = re.match(r'^"?([^"<]+)"?\s*<([^>]+)>', address_str.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip().lower()
    # Just an email address with no name
    clean = address_str.strip().lower()
    return "", clean


def get_company_inboxes() -> list[str]:
    """
    Returns the list of company email addresses to sync.
    Set COMPANY_INBOXES as a comma-separated list in your environment variables.
    Example: sales@jblines.com,support@jblines.com,billing@jblines.com
    """
    raw = os.environ.get("COMPANY_INBOXES", "")
    return [e.strip() for e in raw.split(",") if e.strip()]
