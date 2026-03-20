"""
AI email classifier using the Claude API.

For each new email, Claude reads the subject + body and returns:
  - category: customer | billing | schedule | general
  - summary: 1-2 sentence summary of what the email is about
  - sentiment: positive | neutral | negative | urgent
  - extracted_data: structured fields relevant to the category
    (e.g. invoice number + amount for billing, meeting date for schedule)
"""

import os
import json
import logging
from datetime import datetime

import anthropic

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

CLASSIFICATION_PROMPT = """You are an intelligent email classifier for a company's internal email hub.

Analyze the email below and return a JSON object with the following fields:

{{
  "category": "customer" | "billing" | "schedule" | "general",
  "summary": "1-2 sentence plain-English summary of what this email is about",
  "sentiment": "positive" | "neutral" | "negative" | "urgent",
  "customer_name": "extracted full name of the customer/contact (or null)",
  "customer_company": "extracted company name (or null)",
  "customer_phone": "extracted phone number (or null)",
  "billing_type": "invoice" | "payment" | "quote" | "overdue" | "refund" | null,
  "billing_amount": 1234.56 | null,
  "billing_currency": "USD" | null,
  "invoice_number": "extracted invoice/PO number (or null)",
  "due_date": "YYYY-MM-DD" | null,
  "meeting_title": "title or purpose of the meeting (or null)",
  "meeting_date": "YYYY-MM-DD" | null,
  "meeting_time": "HH:MM" | null,
  "meeting_duration_minutes": 60 | null,
  "meeting_location": "location or video link (or null)"
}}

Category definitions:
- customer: General inquiry, support request, or relationship email from/to a customer
- billing: Contains invoice, payment confirmation, quote, overdue notice, or financial transaction
- schedule: Contains a meeting request, appointment, calendar invite, or scheduling discussion
- general: Internal email, newsletter, notification, or anything that doesn't fit above

Rules:
- If an email has both billing and scheduling content, pick whichever is the PRIMARY purpose
- Be conservative — only extract data you are confident about, otherwise use null
- Return ONLY valid JSON, no markdown, no explanation

EMAIL TO CLASSIFY:
Subject: {subject}
From: {sender_name} <{sender}>
To: {recipient}
Inbox: {inbox}

Body:
{body}
"""


async def classify_email(email_data: dict) -> dict:
    """
    Send an email to Claude for classification.
    Returns a dict of classification results.
    """
    body = email_data.get("body_text") or email_data.get("body_snippet") or ""

    prompt = CLASSIFICATION_PROMPT.format(
        subject=email_data.get("subject", ""),
        sender=email_data.get("sender", ""),
        sender_name=email_data.get("sender_name", ""),
        recipient=email_data.get("recipient", ""),
        inbox=email_data.get("inbox", ""),
        body=body[:3000],  # Limit body length for classification
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Parse the JSON response
        result = json.loads(response_text)
        result["classified_at"] = datetime.utcnow().isoformat()
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON for email {email_data.get('id')}: {e}")
        return {
            "category": "general",
            "summary": email_data.get("body_snippet", ""),
            "sentiment": "neutral",
            "classified_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Classification error for email {email_data.get('id')}: {e}")
        return {
            "category": "general",
            "summary": "",
            "sentiment": "neutral",
            "classified_at": datetime.utcnow().isoformat(),
        }


async def answer_question(question: str, context_emails: list[dict]) -> str:
    """
    Answer a free-form question about the company's emails using Claude.
    Used by the /api/chat endpoint.
    """
    # Build a context string from the most relevant emails
    email_context = ""
    for i, email in enumerate(context_emails[:20], 1):  # Limit to 20 emails
        email_context += f"""
Email #{i}:
- From: {email.get('sender_name', '')} <{email.get('sender', '')}>
- Subject: {email.get('subject', '')}
- Date: {email.get('received_at', '')}
- Inbox: {email.get('inbox', '')}
- Category: {email.get('category', '')}
- Summary: {email.get('ai_summary', '')}
- Snippet: {email.get('body_snippet', '')}
"""

    system_prompt = """You are an intelligent business assistant with access to a company's email data.
Answer questions clearly and helpfully based on the email context provided.
When referencing specific emails, mention the sender, subject, and date.
If you cannot find the answer in the provided emails, say so clearly.
Be concise but thorough. Format amounts with dollar signs. Format dates in a readable way."""

    user_message = f"""Company email context:
{email_context}

Question: {question}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "I encountered an error while processing your question. Please try again."
