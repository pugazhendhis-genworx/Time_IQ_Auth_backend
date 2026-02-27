from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from src.data.clients.postgres_client import Base
from src.utils.id_generator import generate_prefixed_id


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(
        String(50), primary_key=True, default=lambda: generate_prefixed_id("ROL")
    )

    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")
