"""
SQLAlchemy ORM models for the navigation_history table.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from backend.database.connection import Base


class NavigationHistory(Base):
    """
    Persists the in-memory array state to MySQL.

    NOTE: MySQL is for persistence / auditability only.
          All navigation decisions are made by the Array Algorithm Engine.
    """

    __tablename__ = "navigation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    page_url = Column(String(2048), nullable=False)
    position_index = Column(Integer, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Composite index for fast lookups by session
    __table_args__ = (
        Index("ix_session_position", "session_id", "position_index"),
    )

    def __repr__(self) -> str:
        return (
            f"<NavigationHistory id={self.id} session={self.session_id!r} "
            f"index={self.position_index} url={self.page_url!r} "
            f"current={self.is_current}>"
        )
