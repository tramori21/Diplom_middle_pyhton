from sqlalchemy import Column, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base, IdMixin, TimestampMixin


class Booking(IdMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    event_id = Column(UUID(as_uuid=True), ForeignKey("watch_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)

    event = relationship("WatchEvent", back_populates="bookings")


Index(
    "idx_bookings_unique_active_event_user",
    Booking.event_id,
    Booking.user_id,
    unique=True,
    postgresql_where=text("status = 'active'"),
)
