"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")

    # ── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_pw", sa.Text, nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="sales"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("locale", sa.String(5), nullable=False, server_default="fr"),
        sa.Column("google_access_token", sa.Text),
        sa.Column("google_refresh_token", sa.Text),
        sa.Column("google_token_expiry", sa.DateTime(timezone=True)),
        sa.Column("google_email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── leads ─────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("phone", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(500)),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.String(100)),
        sa.Column("province", sa.String(50), server_default="Québec"),
        sa.Column("postal_code", sa.String(10)),
        sa.Column("latitude", sa.Numeric(10, 8)),
        sa.Column("longitude", sa.Numeric(11, 8)),
        sa.Column("google_place_id", sa.String(255)),
        sa.Column("google_rating", sa.Numeric(2, 1)),
        sa.Column("google_reviews", sa.Integer),
        sa.Column("yelp_url", sa.String(500)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("instagram_handle", sa.String(100)),
        sa.Column("facebook_url", sa.String(500)),
        sa.Column("owner_name", sa.String(255)),
        sa.Column("owner_title", sa.String(100)),
        sa.Column("owner_linkedin", sa.String(500)),
        sa.Column("detected_language", sa.String(5), server_default="fr"),
        sa.Column("status", sa.String(30), nullable=False, server_default="nouveau"),
        sa.Column("ai_score", sa.SmallInteger),
        sa.Column("score_rationale", sa.Text),
        sa.Column("source_flags", postgresql.JSONB, server_default="'[]'::jsonb"),
        sa.Column("business_hours", postgresql.JSONB),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True)),
        sa.Column("next_followup_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_leads_status", "leads", ["status"])
    op.create_index("idx_leads_city", "leads", ["city"])
    op.create_index("idx_leads_industry", "leads", ["industry"])
    op.create_index("idx_leads_google_place_id", "leads", ["google_place_id"], unique=True)
    op.create_index("idx_leads_business_name", "leads", ["business_name"])
    # Full-text search index
    op.execute(
        "CREATE INDEX idx_leads_fts ON leads USING gin("
        "to_tsvector('french', coalesce(business_name, '') || ' ' || coalesce(city, '')))"
    )

    # ── scrape_jobs ────────────────────────────────────────────────────
    op.create_table(
        "scrape_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("sources", postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column("query_term", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("bounding_box", postgresql.JSONB),
        sa.Column("max_results", sa.SmallInteger, server_default="30"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.String(255)),
        sa.Column("leads_found", sa.Integer, server_default="0"),
        sa.Column("leads_new", sa.Integer, server_default="0"),
        sa.Column("leads_merged", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_scrape_jobs_status", "scrape_jobs", ["status"])

    # ── lead_sources ───────────────────────────────────────────────────
    op.create_table(
        "lead_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE")),
        sa.Column("scrape_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scrape_jobs.id", ondelete="SET NULL")),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("raw_data", postgresql.JSONB, nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_lead_sources_lead_id", "lead_sources", ["lead_id"])
    op.create_index("idx_lead_sources_source", "lead_sources", ["source"])

    # ── campaigns ─────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("template_subject", sa.Text),
        sa.Column("template_body", sa.Text),
        sa.Column("industry_target", sa.String(100)),
        sa.Column("language", sa.String(5), server_default="fr"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ── messages ──────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL")),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False, server_default="outbound"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("subject", sa.Text),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("ai_generated", sa.Boolean, server_default="true"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("twilio_sid", sa.String(100)),
        sa.Column("gmail_message_id", sa.String(255)),
        sa.Column("gmail_thread_id", sa.String(255)),
        sa.Column("reply_to_message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id")),
        sa.Column("ai_reply_suggestion", sa.Text),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_messages_lead", "messages", ["lead_id"])
    op.create_index("idx_messages_status", "messages", ["status"])
    op.create_index("idx_messages_channel", "messages", ["channel"])
    op.create_index("idx_messages_gmail_thread", "messages", ["gmail_thread_id"])

    # ── interactions ───────────────────────────────────────────────────
    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="SET NULL")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_interactions_lead", "interactions", ["lead_id"])
    op.create_index("idx_interactions_type", "interactions", ["type"])

    # ── calendar_events ────────────────────────────────────────────────
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_event_id", sa.String(255)),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(30), server_default="rdv"),
        sa.Column("location", sa.Text),
        sa.Column("meet_link", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_calendar_events_lead", "calendar_events", ["lead_id"])
    op.create_index("idx_calendar_events_google_id", "calendar_events", ["google_event_id"])


def downgrade() -> None:
    op.drop_table("calendar_events")
    op.drop_table("interactions")
    op.drop_table("messages")
    op.drop_table("campaigns")
    op.drop_table("lead_sources")
    op.drop_table("scrape_jobs")
    op.drop_table("leads")
    op.drop_table("users")
