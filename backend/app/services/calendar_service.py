"""Google Calendar service — create, update, delete events."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.logging import logger

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lead import Lead
    from app.models.calendar_event import CalendarEvent


def _build_service(user: "User"):
    from google.oauth2.credentials import Credentials
    from app.config import settings

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


async def create_rdv_event(
    user: "User",
    lead: "Lead",
    start_time: datetime,
    duration_minutes: int = 30,
    title: str | None = None,
    description: str | None = None,
    location: str | None = None,
    add_meet: bool = True,
) -> dict:
    """
    Create a Google Calendar RDV event for a lead.
    Returns dict with google_event_id, html_link, meet_link.
    """
    if not user.google_access_token:
        raise ValueError("User has no Google token")

    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(minutes=duration_minutes)

    event_title = title or f"RDV — {lead.business_name}"
    event_description = description or (
        f"Prospection HGI Digital\n"
        f"Entreprise : {lead.business_name}\n"
        f"Secteur : {lead.industry or 'N/A'}\n"
        f"Contact : {lead.phone or lead.email or 'N/A'}\n"
        f"Ville : {lead.city or 'N/A'}"
    )

    event_body: dict = {
        "summary": event_title,
        "description": event_description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "America/Toronto",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "America/Toronto",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 15},
            ],
        },
    }

    if location:
        event_body["location"] = location
    elif lead.address:
        event_body["location"] = f"{lead.address}, {lead.city}"

    if add_meet:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": f"hgi-{lead.id}-{int(start_time.timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    try:
        service = _build_service(user)
        conference_version = 1 if add_meet else 0
        created = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=conference_version,
        ).execute()

        meet_link = None
        if add_meet:
            conf_data = created.get("conferenceData", {})
            for ep in conf_data.get("entryPoints", []):
                if ep.get("entryPointType") == "video":
                    meet_link = ep.get("uri")
                    break

        logger.info("calendar_event_created", event_id=created["id"], lead_id=str(lead.id))
        return {
            "google_event_id": created["id"],
            "html_link": created.get("htmlLink"),
            "meet_link": meet_link,
        }
    except HttpError as exc:
        logger.error("calendar_create_failed", error=str(exc), lead_id=str(lead.id))
        raise


async def create_followup_event(
    user: "User",
    lead: "Lead",
    followup_at: datetime,
) -> dict:
    """Create a follow-up reminder event."""
    return await create_rdv_event(
        user=user,
        lead=lead,
        start_time=followup_at,
        duration_minutes=15,
        title=f"Relance — {lead.business_name}",
        description=f"Rappel de suivi pour {lead.business_name} ({lead.city})\nStatut actuel : {lead.status}",
        add_meet=False,
    )


async def delete_event(user: "User", google_event_id: str) -> None:
    """Delete a Google Calendar event."""
    try:
        service = _build_service(user)
        service.events().delete(calendarId="primary", eventId=google_event_id).execute()
        logger.info("calendar_event_deleted", event_id=google_event_id)
    except HttpError as exc:
        logger.debug("calendar_delete_failed", error=str(exc))


async def list_upcoming_events(user: "User", max_results: int = 10) -> list[dict]:
    """List upcoming calendar events for the user."""
    try:
        service = _build_service(user)
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        return [
            {
                "id": e.get("id"),
                "title": e.get("summary"),
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end": e["end"].get("dateTime", e["end"].get("date")),
                "html_link": e.get("htmlLink"),
                "meet_link": next(
                    (ep["uri"] for ep in e.get("conferenceData", {}).get("entryPoints", []) if ep.get("entryPointType") == "video"),
                    None,
                ),
            }
            for e in events
        ]
    except HttpError as exc:
        logger.error("calendar_list_failed", error=str(exc))
        return []
