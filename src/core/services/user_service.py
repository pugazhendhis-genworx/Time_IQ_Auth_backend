from fastapi import HTTPException

from src.data.models.postgres.user_model import User
from src.data.repositories.role_repository import (
    get_all_roles,
    get_role_by_name,
)
from src.data.repositories.user_repository import (
    get_all_users,
    get_user_by_email,
    get_user_by_id,
)
from src.observability.logging import logging
from src.utils.password_hashing import hash_password

logger = logging.get_logger(__name__)


async def get_all_users_service(db):
    """
    Retrieve all users from the database with their basic details and roles.
    """
    logger.info("Retrieving all users from database")
    users = await get_all_users(db)
    return [
        {
            "user_id": u.user_id,
            "name": u.name,
            "email": u.email,
            "contact_no": u.contact_no,
            "status": u.status,
            "role": u.role.name if u.role else None,
            "created_at": u.created_at,
        }
        for u in users
    ]


async def get_user_by_id_service(db, user_id: str):
    """
    Retrieve a specific user by their ID along with role details.
    """
    logger.info(f"Retrieving user with id: {user_id}")
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "contact_no": user.contact_no,
        "status": user.status,
        "role": user.role.name if user.role else None,
        "created_at": user.created_at,
    }


async def add_user_service(db, payload):
    """
    Directly add a new user to the database with a specific role, skipping
    the standard signup flow constraints (useful for admin creation).
    """
    logger.info(
        f"Attempting to add new user: {payload.email} with role: {payload.role_name}"
    )
    existing = await get_user_by_email(db, payload.email)
    if existing:
        logger.warning(f"Add user failed: Email already registered {payload.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    role = await get_role_by_name(db, payload.role_name)
    if not role:
        logger.warning(f"Add user failed: Role '{payload.role_name}' not found")
        raise HTTPException(
            status_code=400,
            detail=f"Role '{payload.role_name}' not found",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        contact_no=payload.contact_no,
        password=hash_password(payload.password),
        role_id=role.role_id,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user.user_id} added successfully with role {role.name}")
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "contact_no": user.contact_no,
        "status": user.status,
        "role": role.name,
        "created_at": user.created_at,
    }


async def get_all_roles_service(db):
    """
    Retrieve all available system roles.
    """
    logger.info("Retrieving all roles")
    roles = await get_all_roles(db)
    return [{"role_id": r.role_id, "name": r.name} for r in roles]
