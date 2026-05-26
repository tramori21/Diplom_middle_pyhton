"""initial booking schema

Revision ID: 20260526_0001
Revises:
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260526_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watch_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("movie_id", sa.String(length=255), nullable=False),
        sa.Column("movie_title", sa.String(length=512), nullable=True),
        sa.Column("host_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("place", sa.String(length=512), nullable=False),
        sa.Column("seats_limit", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("idx_watch_events_movie_id", "watch_events", ["movie_id"])
    op.create_index("idx_watch_events_starts_at", "watch_events", ["starts_at"])
    op.create_index("idx_watch_events_status", "watch_events", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watch_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("idx_bookings_event_id", "bookings", ["event_id"])
    op.create_index("idx_bookings_user_id", "bookings", ["user_id"])
    op.create_index(
        "idx_bookings_unique_active_event_user",
        "bookings",
        ["event_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("idx_bookings_unique_active_event_user", table_name="bookings")
    op.drop_index("idx_bookings_user_id", table_name="bookings")
    op.drop_index("idx_bookings_event_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("idx_watch_events_status", table_name="watch_events")
    op.drop_index("idx_watch_events_starts_at", table_name="watch_events")
    op.drop_index("idx_watch_events_movie_id", table_name="watch_events")
    op.drop_table("watch_events")
