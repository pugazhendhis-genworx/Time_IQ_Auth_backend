from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from src.data.clients.postgres_client import Base
from src.utils.id_generator import generate_prefixed_id


class User(Base):
    __tablename__ = "users"
    user_id = Column(
        String(50),
        unique=True,
        index=True,
        primary_key=True,
        default=lambda: generate_prefixed_id("USR"),
    )
    name = Column(String(100))
    email = Column(String(150), unique=True, index=True)
    contact_no = Column(String(50))
    password = Column(String(255))
    status = Column(String(50), default="ACTIVE")
    role_id = Column(
        String(50),
        ForeignKey("roles.role_id", ondelete="SET NULL"),
    )
    created_at = Column(DateTime, server_default=func.now())
    role = relationship("Role", back_populates="users")
    sessions = relationship("Session", back_populates="user")
