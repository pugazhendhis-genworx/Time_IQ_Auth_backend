from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_db
from src.core.services.user_service import (
    add_user_service,
    get_all_roles_service,
    get_all_users_service,
    get_user_by_id_service,
)
from src.schemas.user_schema import (
    CreateUserRequest,
    RoleOut,
    UserOut,
)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get(
    "/",
    response_model=list[UserOut],
    summary="List All Users",
    description="Retrieve a list of all registered users in the system.",
)
async def get_all_users(db=Depends(get_pg_db)):
    return await get_all_users_service(db)


@user_router.get(
    "/roles",
    response_model=list[RoleOut],
    summary="List Roles",
    description="Fetch all available access roles (Admin, etc.).",
)
async def get_roles(db=Depends(get_pg_db)):
    return await get_all_roles_service(db)


@user_router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get User By ID",
    description="Retrieve detailed information about a specific user using their ID.",
)
async def get_user(user_id: str, db=Depends(get_pg_db)):
    return await get_user_by_id_service(db, user_id)


@user_router.post(
    "/",
    response_model=UserOut,
    status_code=201,
    summary="Create New User",
    description="Admin endpoint to bypass normal sign-up and directly provision a user account.",
)
async def add_user(
    payload: CreateUserRequest,
    db=Depends(get_pg_db),
):
    return await add_user_service(db, payload)
