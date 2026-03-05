from sqlalchemy import select

from src.data.models.postgres.role_model import Role


async def get_role_by_name(db, name: str):
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def get_role_by_id(db, role_id: str):
    result = await db.execute(select(Role).where(Role.role_id == role_id))
    return result.scalar_one_or_none()


async def get_all_roles(db):
    result = await db.execute(select(Role))
    return result.scalars().all()
