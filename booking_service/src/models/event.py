from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base, IdMixin, TimestampMixin


class WatchEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "watch_events"

    movie_id = Column(String(255), nullable=False, index=True)
    movie_title = Column(String(512), nullable=True)
    host_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    place = Column(String(512), nullable=False)
    seats_limit = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active", index=True)

    bookings = relationship("Booking", back_populates="event", cascade="all, delete-orphan")
