from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.lead import Lead
from app.models.interaction import Interaction
from app.schemas.lead import LeadCreate, LeadUpdate
from app.core.exceptions import NotFoundError


class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, lead_id: UUID) -> Lead:
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            raise NotFoundError("Lead")
        return lead

    async def list(
        self,
        *,
        status: str | None = None,
        city: str | None = None,
        industry: str | None = None,
        score_min: int | None = None,
        score_max: int | None = None,
        search: str | None = None,
        assigned_to: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Lead]:
        filters = []
        if status:
            filters.append(Lead.status == status)
        if city:
            filters.append(Lead.city.ilike(f"%{city}%"))
        if industry:
            filters.append(Lead.industry == industry)
        if score_min is not None:
            filters.append(Lead.ai_score >= score_min)
        if score_max is not None:
            filters.append(Lead.ai_score <= score_max)
        if assigned_to:
            filters.append(Lead.assigned_to == assigned_to)
        if search:
            filters.append(
                or_(
                    Lead.business_name.ilike(f"%{search}%"),
                    Lead.city.ilike(f"%{search}%"),
                    Lead.owner_name.ilike(f"%{search}%"),
                )
            )

        query = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)
        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def create(self, data: LeadCreate) -> Lead:
        lead = Lead(**data.model_dump())
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def update(self, lead_id: UUID, data: LeadUpdate, user_id: UUID | None = None) -> Lead:
        lead = await self.get(lead_id)
        old_status = lead.status
        updates = data.model_dump(exclude_none=True)

        for field, value in updates.items():
            setattr(lead, field, value)

        lead.updated_at = datetime.now(timezone.utc)

        if "status" in updates and updates["status"] != old_status:
            if updates["status"] == "contacté":
                lead.last_contacted_at = datetime.now(timezone.utc)
            interaction = Interaction(
                lead_id=lead.id,
                user_id=user_id,
                type="status_changed",
                metadata_={"previous_status": old_status, "new_status": updates["status"]},
            )
            self.db.add(interaction)

        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def delete(self, lead_id: UUID) -> None:
        lead = await self.get(lead_id)
        await self.db.delete(lead)
        await self.db.commit()

    async def get_interactions(self, lead_id: UUID) -> list[Interaction]:
        result = await self.db.execute(
            select(Interaction)
            .where(Interaction.lead_id == lead_id)
            .order_by(Interaction.occurred_at.desc())
        )
        return result.scalars().all()

    async def add_note(self, lead_id: UUID, note: str, user_id: UUID) -> Interaction:
        interaction = Interaction(
            lead_id=lead_id,
            user_id=user_id,
            type="note_added",
            notes=note,
        )
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        return interaction

    async def get_pipeline_stats(self) -> dict:
        counts = await self.count_by_status()
        statuses = ["nouveau", "contacté", "réponse", "rdv", "fermé", "perdu"]
        return {s: counts.get(s, 0) for s in statuses}

    async def get_geocoded(self) -> list[Lead]:
        result = await self.db.execute(
            select(Lead).where(Lead.latitude.isnot(None), Lead.longitude.isnot(None))
        )
        return result.scalars().all()
