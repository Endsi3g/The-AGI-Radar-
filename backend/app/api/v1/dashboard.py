"""Dashboard KPI stats endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.lead import Lead
from app.models.message import Message

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

PIPELINE_STATUSES = ["nouveau", "contacté", "réponse", "rdv", "fermé", "perdu"]


@router.get("/stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user=Depends(get_current_user),
):
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

    # Pipeline counts per status
    pipeline_rows = (
        await db.execute(
            select(Lead.status, func.count(Lead.id).label("cnt"))
            .group_by(Lead.status)
        )
    ).all()
    pipeline = {s: 0 for s in PIPELINE_STATUSES}
    total_leads = 0
    for row in pipeline_rows:
        if row.status in pipeline:
            pipeline[row.status] = row.cnt
        total_leads += row.cnt

    # Message counts
    message_rows = (
        await db.execute(
            select(Message.status, func.count(Message.id).label("cnt"))
            .group_by(Message.status)
        )
    ).all()
    msg_by_status: dict[str, int] = {}
    total_messages = 0
    for row in message_rows:
        msg_by_status[row.status] = row.cnt
        total_messages += row.cnt

    # Leads created in the last 30 days
    leads_30d_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= cutoff_30d)
    )
    leads_30d: int = leads_30d_result.scalar_one()

    # Average AI score (non-null only)
    avg_score_result = await db.execute(
        select(func.avg(Lead.ai_score)).where(Lead.ai_score.is_not(None))
    )
    avg_score_raw = avg_score_result.scalar_one()
    avg_score: float | None = float(avg_score_raw) if avg_score_raw is not None else None

    # Conversion rate: leads at "rdv" / total leads
    rdv_count = pipeline.get("rdv", 0)
    conversion_rate: float = round(rdv_count / total_leads, 4) if total_leads > 0 else 0.0

    # Top 5 cities
    top_cities_rows = (
        await db.execute(
            select(Lead.city, func.count(Lead.id).label("cnt"))
            .where(Lead.city.is_not(None))
            .group_by(Lead.city)
            .order_by(func.count(Lead.id).desc())
            .limit(5)
        )
    ).all()
    top_cities = [{"city": row.city, "count": row.cnt} for row in top_cities_rows]

    # Top 5 industries
    top_industries_rows = (
        await db.execute(
            select(Lead.industry, func.count(Lead.id).label("cnt"))
            .where(Lead.industry.is_not(None))
            .group_by(Lead.industry)
            .order_by(func.count(Lead.id).desc())
            .limit(5)
        )
    ).all()
    top_industries = [{"industry": row.industry, "count": row.cnt} for row in top_industries_rows]

    return {
        "pipeline": pipeline,
        "messages": {
            "pending_approval": msg_by_status.get("pending_approval", 0),
            "sent": msg_by_status.get("sent", 0),
            "total": total_messages,
        },
        "leads_30d": leads_30d,
        "avg_score": avg_score,
        "conversion_rate": conversion_rate,
        "top_cities": top_cities,
        "top_industries": top_industries,
    }
