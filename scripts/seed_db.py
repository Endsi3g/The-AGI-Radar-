#!/usr/bin/env python3
"""
Seed script — creates initial admin user and sample leads.
Run: docker compose exec backend python /app/../scripts/seed_db.py
Or: DATABASE_URL_SYNC=... python scripts/seed_db.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.lead import Lead
from app.core.security import hash_password
from app.database import Base

engine = create_engine(settings.database_url_sync)


def seed():
    with Session(engine) as session:
        # Check if admin already exists
        existing = session.query(User).filter_by(email="admin@hgiradar.com").first()
        if existing:
            print("Admin user already exists. Skipping seed.")
            return

        # Create admin user
        admin = User(
            email="admin@hgiradar.com",
            full_name="Admin HGI",
            hashed_pw=hash_password("hgi2026!"),
            role="admin",
            locale="fr",
        )
        session.add(admin)

        # Create sample leads
        sample_leads = [
            Lead(
                business_name="Pizzeria Napoli",
                industry="restaurant",
                city="Montréal",
                province="Québec",
                phone="514-555-0101",
                address="1234 rue Sainte-Catherine, Montréal, QC",
                latitude=45.5088,
                longitude=-73.5878,
                google_rating=4.2,
                google_reviews=87,
                detected_language="fr",
                status="nouveau",
                source_flags=["google_maps"],
            ),
            Lead(
                business_name="Plomberie Côté",
                industry="plombier",
                city="Laval",
                province="Québec",
                phone="450-555-0202",
                website="https://plomberie-cote.ca",
                latitude=45.5717,
                longitude=-73.7243,
                google_rating=4.7,
                google_reviews=34,
                detected_language="fr",
                status="nouveau",
                source_flags=["pages_jaunes"],
            ),
            Lead(
                business_name="Café Saint-Henri",
                industry="restaurant",
                city="Montréal",
                province="Québec",
                phone="514-555-0303",
                latitude=45.4756,
                longitude=-73.5801,
                google_rating=4.5,
                google_reviews=142,
                detected_language="fr",
                status="nouveau",
                source_flags=["google_maps", "yelp"],
            ),
        ]
        session.add_all(sample_leads)
        session.commit()

        print("✓ Admin user created: admin@hgiradar.com / hgi2026!")
        print(f"✓ {len(sample_leads)} sample leads created")


if __name__ == "__main__":
    seed()
