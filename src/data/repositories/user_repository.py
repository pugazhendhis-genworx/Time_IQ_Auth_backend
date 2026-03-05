from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.data.models.postgres.user_model import User
from src.utils.password_hashing import hash_password


async def get_user_by_email(db, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db, user_id: str):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_user_password_by_email(db, email: str, new_password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None
    hashed_pw = hash_password(new_password)
    user.password = hashed_pw
    await db.commit()
    await db.refresh(user)

    return user


async def get_all_users(db):
    result = await db.execute(select(User).options(selectinload(User.role)))
    return result.scalars().all()


async def create_user(db, user: User):
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
