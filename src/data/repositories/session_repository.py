from sqlalchemy import select, update

from src.data.models.postgres.session_model import Session


async def get_session_by_jti(db, jti: str):
    result = await db.execute(select(Session).where(Session.jti == jti))
    return result.scalar_one_or_none()


async def revoke_session(db, jti: str):
    await db.execute(update(Session).where(Session.jti == jti).values(is_revoked=True))
    await db.commit()


async def revoke_all_user_sessions(db, user_id: str):
    await db.execute(
        update(Session).where(Session.user_id == user_id).values(is_revoked=True)
    )
    await db.commit()


async def create_session(db, session: Session):
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
