"""Twilio service — SMS sending and Voice call initiation."""
from __future__ import annotations

from app.config import settings
from app.core.logging import logger


def _client():
    from twilio.rest import Client  # type: ignore
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


async def send_sms(to_number: str, body: str) -> dict:
    """
    Send an SMS via Twilio.
    Returns dict with twilio_sid and status.
    """
    if not settings.twilio_account_sid or not settings.twilio_from_number:
        raise ValueError("Twilio credentials not configured")

    try:
        client = _client()
        message = client.messages.create(
            to=to_number,
            from_=settings.twilio_from_number,
            body=body[:1600],  # Twilio max
        )
        logger.info("twilio_sms_sent", sid=message.sid, to=to_number)
        return {
            "twilio_sid": message.sid,
            "status": message.status,
        }
    except Exception as exc:
        logger.error("twilio_sms_failed", error=str(exc), to=to_number)
        raise


async def initiate_call(to_number: str, script_url: str) -> dict:
    """
    Initiate an outbound VoIP call via Twilio.
    script_url: publicly accessible TwiML URL for the call flow.
    Returns dict with call_sid.
    """
    if not settings.twilio_account_sid or not settings.twilio_from_number:
        raise ValueError("Twilio credentials not configured")

    try:
        client = _client()
        call = client.calls.create(
            to=to_number,
            from_=settings.twilio_from_number,
            url=script_url,
            record=True,
            recording_status_callback=f"{settings.google_redirect_uri.rsplit('/google', 1)[0]}/comms/voice/recording-callback",
        )
        logger.info("twilio_call_initiated", sid=call.sid, to=to_number)
        return {
            "call_sid": call.sid,
            "status": call.status,
        }
    except Exception as exc:
        logger.error("twilio_call_failed", error=str(exc), to=to_number)
        raise


def parse_inbound_sms(form_data: dict) -> dict:
    """Parse Twilio inbound SMS webhook payload."""
    return {
        "from_number": form_data.get("From", ""),
        "to_number": form_data.get("To", ""),
        "body": form_data.get("Body", ""),
        "twilio_sid": form_data.get("MessageSid", ""),
        "num_media": int(form_data.get("NumMedia", 0)),
    }


def parse_call_status(form_data: dict) -> dict:
    """Parse Twilio call status callback payload."""
    return {
        "call_sid": form_data.get("CallSid", ""),
        "call_status": form_data.get("CallStatus", ""),
        "from_number": form_data.get("From", ""),
        "to_number": form_data.get("To", ""),
        "duration": form_data.get("CallDuration", ""),
        "recording_url": form_data.get("RecordingUrl", ""),
    }


def parse_recording_callback(form_data: dict) -> dict:
    """Parse Twilio recording status callback."""
    return {
        "call_sid": form_data.get("CallSid", ""),
        "recording_sid": form_data.get("RecordingSid", ""),
        "recording_url": form_data.get("RecordingUrl", ""),
        "recording_duration": form_data.get("RecordingDuration", ""),
        "recording_status": form_data.get("RecordingStatus", ""),
    }
