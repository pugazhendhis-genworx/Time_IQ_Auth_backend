from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy import select

from src.core.services.jwt_service import decode_access_token
from src.data.clients.postgres_client import get_pg_session
from src.data.models.postgres.role_model import Role
from src.data.models.postgres.user_model import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes={
        "admin": "Admin access",
        "operation_executive": "Operation executive access",
        "auditor": "Auditor access",
    },
)


async def get_pg_db():
    async for session in get_pg_session():
        yield session


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Security(oauth2_scheme),
    db=Depends(get_pg_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    payload = decode_access_token(token)

    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.role_id)
        .where(User.user_id == user_id)
    )

    row = result.first()

    if not row:
        raise credentials_exception

    user, role = row

    for scope in security_scopes.scopes:
        if scope != role.name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {scope}",
            )

    return {
        "user_id": user.user_id,
        "email": user.email,
        "role_id": role.role_id,
        "role_name": role.name,
    }
