import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from jose import jwt

from src.config.settings import settings


def create_access_token(user_id: str):
    try:
        payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(UTC)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "type": "access",
        }
        return jwt.encode(
            payload, settings.ACCESS_SECRET_KEY, algorithm=settings.ALGORITHM
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def create_refresh_token(user_id: str):
    try:
        payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            "type": "refresh",
        }
        return jwt.encode(
            payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error creating refresh token"
        ) from e


def decode_refresh_token(token: str):
    try:
        return jwt.decode(
            token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def decode_access_token(token: str):
    try:
        return jwt.decode(
            token, settings.ACCESS_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid access token") from e
