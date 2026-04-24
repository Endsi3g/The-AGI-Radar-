"""Lead scoring service — heuristic fast path + async AI path."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.lead import Lead
from app.models.interaction import Interaction
from datetime import datetime, timezone


def heuristic_score(lead: Lead) -> tuple[int, str]:
    """
    Fast synchronous heuristic scoring.
    Returns (score 0-100, rationale).
    Used as fallback when Ollama is unavailable.
    """
    score = 40
    reasons: list[str] = []

    if not lead.website:
        score += 25
        reasons.append("Site web absent (+25)")
    elif lead.website:
        score += 5
        reasons.append("Site web présent (+5)")

    rating = float(lead.google_rating or 0)
    reviews = int(lead.google_reviews or 0)

    if rating >= 4.0:
        score += 20
        reasons.append(f"Bonne note Google {rating}/5 (+20)")
    elif rating > 0 and rating < 3.0:
        score -= 10
        reasons.append(f"Note Google faible {rating}/5 (-10)")

    if reviews >= 50:
        score += 15
        reasons.append(f"{reviews} avis Google (+15)")
    elif reviews >= 20:
        score += 8
        reasons.append(f"{reviews} avis Google (+8)")

    if lead.owner_name:
        score += 10
        reasons.append("Décideur identifié (+10)")

    if not lead.email:
        score -= 15
        reasons.append("Email absent (-15)")

    if lead.instagram_handle and not lead.website:
        score += 5
        reasons.append("Instagram sans site web (+5)")

    priority_industries = {"restaurant", "café", "cafe", "hôtel", "hotel", "coiffeur", "spa", "gym", "bar"}
    industry = (lead.industry or "").lower()
    if any(p in industry for p in priority_industries):
        score += 15
        reasons.append(f"Secteur prioritaire {lead.industry} (+15)")

    score = max(0, min(100, score))
    rationale = " — ".join(reasons[:4]) if reasons else "Score standard."
    return score, rationale


async def score_with_ai(lead: Lead) -> tuple[int, str]:
    """Score a lead using AI with heuristic fallback."""
    from app.services.ai_service import score_lead

    lead_dict = {
        "business_name": lead.business_name,
        "industry": lead.industry,
        "city": lead.city,
        "google_rating": float(lead.google_rating) if lead.google_rating else None,
        "google_reviews": lead.google_reviews,
        "website": lead.website,
        "email": lead.email,
        "owner_name": lead.owner_name,
        "instagram_handle": lead.instagram_handle,
        "description": lead.description,
        "detected_language": lead.detected_language,
    }

    try:
        result = await score_lead(lead_dict)
        return result.score, result.rationale
    except Exception as exc:
        logger.warning("ai_scoring_fallback", error=str(exc), lead_id=str(lead.id))
        return heuristic_score(lead)


async def apply_score(lead: Lead, db: AsyncSession, use_ai: bool = True) -> Lead:
    """Score and persist to the lead record, log an interaction."""
    if use_ai:
        score, rationale = await score_with_ai(lead)
    else:
        score, rationale = heuristic_score(lead)

    lead.ai_score = score
    lead.score_rationale = rationale
    lead.updated_at = datetime.now(timezone.utc)

    interaction = Interaction(
        lead_id=lead.id,
        type="score_updated",
        notes=f"Score IA : {score}/100 — {rationale[:200]}",
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(lead)
    return lead
