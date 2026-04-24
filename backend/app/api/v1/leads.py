from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database import get_db
from app.models.lead import Lead
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadGeoJSON
from app.dependencies import get_current_user, require_role
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: str | None = Query(None, alias="status"),
    city: str | None = None,
    industry: str | None = None,
    score_min: int | None = None,
    score_max: int | None = None,
    search: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    filters = []
    if status_filter:
        filters.append(Lead.status == status_filter)
    if city:
        filters.append(Lead.city.ilike(f"%{city}%"))
    if industry:
        filters.append(Lead.industry == industry)
    if score_min is not None:
        filters.append(Lead.ai_score >= score_min)
    if score_max is not None:
        filters.append(Lead.ai_score <= score_max)
    if search:
        filters.append(
            or_(
                Lead.business_name.ilike(f"%{search}%"),
                Lead.city.ilike(f"%{search}%"),
                Lead.owner_name.ilike(f"%{search}%"),
            )
        )

    # Sales see only assigned leads; admin/viewer see all
    if current_user.role == "sales":
        filters.append(Lead.assigned_to == current_user.id)

    query = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    body: LeadCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    lead = Lead(**body.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/map", response_model=list[LeadGeoJSON])
async def leads_for_map(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Lead).where(Lead.latitude.isnot(None), Lead.longitude.isnot(None))
    )
    return result.scalars().all()


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    body: LeadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead")

    old_status = lead.status
    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(lead, field, value)

    lead.updated_at = datetime.now(timezone.utc)

    # Log status change interaction
    if "status" in updates and updates["status"] != old_status:
        interaction = Interaction(
            lead_id=lead.id,
            user_id=current_user.id,
            type="status_changed",
            metadata_={"previous_status": old_status, "new_status": updates["status"]},
        )
        db.add(interaction)

    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("admin"))],
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead")
    await db.delete(lead)
    await db.commit()


@router.get("/{lead_id}/interactions", response_model=list[dict])
async def get_lead_interactions(
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Interaction)
        .where(Interaction.lead_id == lead_id)
        .order_by(Interaction.occurred_at.desc())
    )
    interactions = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "type": i.type,
            "notes": i.notes,
            "metadata": i.metadata_,
            "occurred_at": i.occurred_at.isoformat(),
        }
        for i in interactions
    ]


@router.post("/{lead_id}/interactions", status_code=status.HTTP_201_CREATED)
async def add_interaction(
    lead_id: UUID,
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    interaction = Interaction(
        lead_id=lead_id,
        user_id=current_user.id,
        type=body.get("type", "note_added"),
        notes=body.get("notes"),
    )
    db.add(interaction)
    await db.commit()
    return {"status": "ok"}
