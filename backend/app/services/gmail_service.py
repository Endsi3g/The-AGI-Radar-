"""Gmail API service — send emails, poll inbox for replies."""
from __future__ import annotations

import base64
import email as email_lib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings
from app.core.logging import logger

if TYPE_CHECKING:
    from app.models.user import User


_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://mail.google.com/",
]


def _build_credentials(user: "User") -> Credentials:
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=_SCOPES,
    )
    if user.google_token_expiry:
        creds.expiry = user.google_token_expiry
    return creds


async def refresh_token_if_needed(user: "User", db) -> "User":
    """Refresh Google OAuth token if it expires within 5 minutes."""
    if not user.google_refresh_token:
        return user

    now = datetime.now(timezone.utc)
    expiry = user.google_token_expiry
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry and expiry > now + timedelta(minutes=5):
        return user  # Still valid

    try:
        creds = _build_credentials(user)
        creds.refresh(Request())
        user.google_access_token = creds.token
        if creds.expiry:
            user.google_token_expiry = creds.expiry.replace(tzinfo=timezone.utc)
        user.updated_at = now
        await db.commit()
        await db.refresh(user)
        logger.info("gmail_token_refreshed", user_id=str(user.id))
    except Exception as exc:
        logger.error("gmail_token_refresh_failed", error=str(exc), user_id=str(user.id))

    return user


def _make_mime_message(
    to: str,
    subject: str,
    body: str,
    from_email: str,
    reply_to_thread_id: str | None = None,
) -> dict:
    """Build a base64url-encoded RFC 2822 message dict for the Gmail API."""
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = from_email
    msg["Subject"] = subject

    # Plain text + HTML versions
    text_part = MIMEText(body, "plain", "utf-8")
    html_body = body.replace("\n", "<br>")
    html_part = MIMEText(
        f"<html><body><p style='font-family:sans-serif;line-height:1.6'>{html_body}</p></body></html>",
        "html",
        "utf-8",
    )
    msg.attach(text_part)
    msg.attach(html_part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result: dict = {"raw": raw}
    if reply_to_thread_id:
        result["threadId"] = reply_to_thread_id
    return result


async def send_email(
    user: "User",
    to_email: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> dict:
    """
    Send an email via the user's Gmail account.
    Returns dict with gmail_message_id and gmail_thread_id.
    """
    creds = _build_credentials(user)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    from_email = user.google_email or "me"
    mime_msg = _make_mime_message(to_email, subject, body, from_email, thread_id)

    try:
        sent = service.users().messages().send(userId="me", body=mime_msg).execute()
        logger.info("gmail_sent", message_id=sent["id"], thread_id=sent.get("threadId"))
        return {
            "gmail_message_id": sent["id"],
            "gmail_thread_id": sent.get("threadId"),
        }
    except HttpError as exc:
        logger.error("gmail_send_failed", error=str(exc))
        raise


async def poll_inbox(user: "User", since_history_id: str | None = None) -> list[dict]:
    """
    Fetch unread messages in the inbox. Returns list of dicts:
    {message_id, thread_id, from, subject, body, received_at}
    """
    if not user.google_access_token:
        return []

    creds = _build_credentials(user)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    try:
        query = "is:unread in:inbox"
        list_result = service.users().messages().list(
            userId="me", q=query, maxResults=20
        ).execute()

        messages = list_result.get("messages", [])
        result = []

        for msg_ref in messages:
            try:
                msg = service.users().messages().get(
                    userId="me", id=msg_ref["id"], format="full"
                ).execute()

                headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
                body = _extract_body(msg)

                result.append({
                    "gmail_message_id": msg["id"],
                    "gmail_thread_id": msg.get("threadId"),
                    "from_email": headers.get("from", ""),
                    "subject": headers.get("subject", ""),
                    "body": body,
                    "received_at": datetime.fromtimestamp(
                        int(msg.get("internalDate", 0)) / 1000, tz=timezone.utc
                    ).isoformat(),
                })
            except Exception as exc:
                logger.debug("gmail_message_fetch_error", error=str(exc))
                continue

        return result

    except HttpError as exc:
        logger.error("gmail_poll_failed", error=str(exc))
        return []


def _extract_body(msg: dict) -> str:
    """Extract plain text body from a Gmail message payload."""
    payload = msg.get("payload", {})

    def _decode(data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        except Exception:
            return ""

    # Single part
    if "body" in payload and payload["body"].get("data"):
        return _decode(payload["body"]["data"])

    # Multipart — prefer text/plain
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return _decode(data)

    # Fallback: first part with data
    for part in payload.get("parts", []):
        data = part.get("body", {}).get("data", "")
        if data:
            return _decode(data)

    return ""


async def mark_as_read(user: "User", message_id: str) -> None:
    """Remove UNREAD label from a Gmail message."""
    creds = _build_credentials(user)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as exc:
        logger.debug("gmail_mark_read_failed", error=str(exc))
