"""Google OAuth 2.0 flow + Calendar endpoints."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.calendar_event import CalendarEvent
from app.dependencies import get_current_user
from app.core.logging import logger
from app.services.calendar_service import list_upcoming_events, create_rdv_event, delete_event
from app.core.security import create_access_token
from app.config import settings

router = APIRouter(prefix="/google", tags=["google"])


def _build_oauth_client():
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar",
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


@router.get("/auth-url")
async def get_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return the Google OAuth consent URL. The state encodes the user ID as a short-lived token."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth non configuré")

    state = create_access_token({"sub": str(current_user.id), "purpose": "google_oauth"}, expire_minutes=10)
    flow = _build_oauth_client()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Exchange the authorization code for tokens and store them on the user."""
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("purpose") != "google_oauth":
            raise ValueError("Invalid state purpose")
        user_id = UUID(payload["sub"])
    except (JWTError, ValueError, KeyError) as exc:
        logger.warning("google_oauth_invalid_state", error=str(exc))
        raise HTTPException(status_code=400, detail="État OAuth invalide ou expiré")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    try:
        flow = _build_oauth_client()
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Fetch Google email via userinfo
        import httpx
        resp = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=10,
        )
        google_email = resp.json().get("email") if resp.status_code == 200 else None

        user.google_access_token = creds.token
        user.google_refresh_token = creds.refresh_token
        user.google_token_expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
        user.google_email = google_email
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info("google_oauth_connected", user_id=str(user.id), google_email=google_email)

    except Exception as exc:
        logger.error("google_oauth_callback_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Échec de la connexion Google")

    # Redirect back to the integrations settings page
    frontend_url = settings.cors_origins.split(",")[0].strip()
    return RedirectResponse(url=f"{frontend_url}/settings/integrations?connected=1")


@router.delete("/disconnect")
async def disconnect_google(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Clear Google OAuth tokens for the current user."""
    current_user.google_access_token = None
    current_user.google_refresh_token = None
    current_user.google_token_expiry = None
    current_user.google_email = None
    current_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info("google_disconnected", user_id=str(current_user.id))
    return {"status": "disconnected"}


@router.get("/status")
async def google_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return whether the current user has Google connected."""
    return {
        "connected": current_user.google_connected,
        "google_email": current_user.google_email,
        "token_expiry": current_user.google_token_expiry.isoformat() if current_user.google_token_expiry else None,
    }


@router.get("/calendar/events")
async def get_calendar_events(
    current_user: Annotated[User, Depends(get_current_user)],
    max_results: int = Query(10, ge=1, le=50),
):
    """List upcoming Google Calendar events for the current user."""
    if not current_user.google_connected:
        raise HTTPException(status_code=400, detail="Compte Google non connecté")
    events = await list_upcoming_events(current_user, max_results=max_results)
    return events


@router.post("/calendar/events")
async def create_calendar_event(
    body: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually create a Google Calendar event and persist it in calendar_events."""
    from app.models.lead import Lead
    from datetime import datetime as dt

    if not current_user.google_connected:
        raise HTTPException(status_code=400, detail="Compte Google non connecté")

    lead_id = body.get("lead_id")
    start_time_str = body.get("start_time")
    if not lead_id or not start_time_str:
        raise HTTPException(status_code=422, detail="lead_id et start_time requis")

    result = await db.execute(select(Lead).where(Lead.id == UUID(lead_id)))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead introuvable")

    start_time = dt.fromisoformat(start_time_str)
    duration = body.get("duration_minutes", 30)
    event_type = body.get("event_type", "rdv")

    result_data = await create_rdv_event(
        user=current_user,
        lead=lead,
        start_time=start_time,
        duration_minutes=duration,
        title=body.get("title"),
        description=body.get("description"),
        add_meet=body.get("add_meet", True),
    )

    cal_event = CalendarEvent(
        lead_id=lead.id,
        user_id=current_user.id,
        google_event_id=result_data["google_event_id"],
        start_time=start_time,
        end_time=start_time + timedelta(minutes=duration),
        event_type=event_type,
    )
    db.add(cal_event)
    await db.commit()

    return result_data


@router.delete("/calendar/events/{google_event_id}")
async def delete_calendar_event(
    google_event_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a Google Calendar event."""
    if not current_user.google_connected:
        raise HTTPException(status_code=400, detail="Compte Google non connecté")

    await delete_event(current_user, google_event_id)

    # Remove from local DB if present
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.google_event_id == google_event_id)
    )
    cal_event = result.scalar_one_or_none()
    if cal_event:
        await db.delete(cal_event)
        await db.commit()

    return {"status": "deleted"}
