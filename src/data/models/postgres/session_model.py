from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from src.data.clients.postgres_client import Base
from src.utils.id_generator import generate_prefixed_id


class Session(Base):
    __tablename__ = "sessions"
    session_id = Column(
        String(50), primary_key=True, default=lambda: generate_prefixed_id("SES")
    )
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"))
    jti = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(255))
    user_agent = Column(String(500))
    is_revoked = Column(Boolean, default=False)
    user = relationship("User", back_populates="sessions")
