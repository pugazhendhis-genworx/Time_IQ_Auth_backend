import asyncio
import logging

from sqlalchemy import select

from src.data.clients.postgres_client import async_session_maker
from src.data.models.postgres.role_model import Role

logger = logging.getLogger(__name__)

SEED_ROLES = [
    {
        "role_id": "ROL_c93d88d8-725f-4157-b334-03b2d390d2f8",
        "name": "admin",
    },
    {
        "role_id": "ROL_e939621c-8559-4913-9465-d88683c93ae3",
        "name": "operation_executive",
    },
    {
        "role_id": "ROL_60efb637-8720-4297-bd05-d0377de2a62a",
        "name": "auditor",
    },
]


async def seed_roles() -> None:
    """Insert default roles if they don't already exist."""
    async with async_session_maker() as session:
        for role_data in SEED_ROLES:
            existing = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if existing.scalar_one_or_none() is None:
                role = Role(**role_data)
                session.add(role)
                await session.flush()
        await session.commit()
        logger.info("Role seed completed — %d roles ensured.", len(SEED_ROLES))


if __name__ == "__main__":
    asyncio.run(seed_roles())
