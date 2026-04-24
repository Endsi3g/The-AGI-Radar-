"""Map endpoints — GeoJSON leads, zone query, OSRM itinerary."""
from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.lead import Lead
from app.models.user import User
from app.dependencies import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/map", tags=["map"])

STATUS_COLORS = {
    "nouveau":   "#3B82F6",
    "contacté":  "#F59E0B",
    "réponse":   "#10B981",
    "rdv":       "#8B5CF6",
    "fermé":     "#6B7280",
    "perdu":     "#EF4444",
}


@router.get("/leads")
async def map_leads(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """GeoJSON FeatureCollection of all geo-located leads."""
    result = await db.execute(
        select(Lead).where(Lead.latitude.isnot(None), Lead.longitude.isnot(None))
    )
    leads = result.scalars().all()

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lead.longitude), float(lead.latitude)],
            },
            "properties": {
                "id": str(lead.id),
                "name": lead.business_name,
                "status": lead.status,
                "city": lead.city or "",
                "industry": lead.industry or "",
                "phone": lead.phone or "",
                "score": lead.ai_score,
                "color": STATUS_COLORS.get(lead.status, "#6B7280"),
            },
        }
        for lead in leads
    ]

    return {"type": "FeatureCollection", "features": features}


def _point_in_polygon(lng: float, lat: float, ring: list[list[float]]) -> bool:
    """Ray casting algorithm — ring coords are [lng, lat]."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


@router.post("/zone-query")
async def zone_query(
    body: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    """Return leads whose [lng,lat] fall inside the given polygon ring."""
    coordinates = body.get("coordinates")
    if not coordinates:
        raise HTTPException(status_code=422, detail="coordinates requis")

    # Accept both [[lng,lat],...] and [[[lng,lat],...]] (GeoJSON Polygon first ring)
    ring: list[list[float]] = coordinates[0] if isinstance(coordinates[0][0], list) else coordinates

    result = await db.execute(
        select(Lead).where(Lead.latitude.isnot(None), Lead.longitude.isnot(None))
    )
    leads = result.scalars().all()

    matched = [
        lead for lead in leads
        if _point_in_polygon(float(lead.longitude), float(lead.latitude), ring)
    ]

    logger.info("map_zone_query", matched=len(matched))
    return {
        "count": len(matched),
        "leads": [
            {
                "id": str(l.id),
                "business_name": l.business_name,
                "status": l.status,
                "city": l.city or "",
                "industry": l.industry or "",
                "phone": l.phone or "",
                "score": l.ai_score,
                "latitude": float(l.latitude),
                "longitude": float(l.longitude),
            }
            for l in matched
        ],
    }


@router.post("/itinerary")
async def optimize_itinerary(
    body: dict,
    _: Annotated[User, Depends(get_current_user)],
):
    """
    Optimize a visit route using OSRM trip service.
    Expects: { coordinates: [[lng, lat], ...], lead_ids: [...] }
    Returns: ordered_indices, duration_seconds, distance_meters, geometry (GeoJSON LineString)
    """
    coords: list[list[float]] = body.get("coordinates", [])
    if len(coords) < 2:
        raise HTTPException(status_code=422, detail="Au moins 2 coordonnées requises")
    if len(coords) > 20:
        raise HTTPException(status_code=422, detail="Maximum 20 arrêts")

    coord_str = ";".join(f"{lng},{lat}" for lng, lat in coords)
    osrm_url = (
        f"http://router.project-osrm.org/trip/v1/driving/{coord_str}"
        "?roundtrip=false&source=first&destination=last"
        "&steps=false&geometries=geojson&overview=full"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(osrm_url)
        data = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"OSRM inaccessible : {exc}")

    if data.get("code") != "Ok":
        raise HTTPException(status_code=502, detail=f"OSRM error : {data.get('code')}")

    trips = data.get("trips", [])
    waypoints = data.get("waypoints", [])

    ordered_indices = sorted(
        range(len(waypoints)),
        key=lambda i: waypoints[i].get("waypoint_index", i),
    )

    return {
        "ordered_indices": ordered_indices,
        "duration_seconds": trips[0]["duration"] if trips else None,
        "distance_meters": trips[0]["distance"] if trips else None,
        "geometry": trips[0]["geometry"] if trips else None,
    }
