from sqlalchemy import select

from src.data.models.postgres.role_model import Role


async def get_role_by_name(db, name: str):
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()
