import random
from datetime import UTC, datetime

from fastapi import HTTPException

from src.core.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from src.data.models.postgres.session_model import Session
from src.data.models.postgres.user_model import User
from src.data.repositories.role_repository import get_role_by_name
from src.data.repositories.session_repository import (
    create_session,
    get_session_by_jti,
    revoke_all_user_sessions,
    revoke_session,
)
from src.data.repositories.user_repository import (
    create_user,
    get_user_by_email,
    update_user_password_by_email,
)
from src.utils.otp_store import set_otp, verify_otp
from src.utils.password_hashing import hash_password, verify_password


async def signup_service(db, user):
    try:
        existing = await get_user_by_email(db, user.email)
        if existing:
            raise HTTPException(400, "Email already registered")
        default_role = await get_role_by_name(db, "admin")
        user_data = User(
            name=user.name,
            email=user.email,
            contact_no=user.contact_no,
            password=hash_password(user.password),
            role_id=default_role.role_id if default_role else None,
        )

        result = await create_user(db, user_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def login_service(db, request, response, username, password):
    try:
        user = await get_user_by_email(db, username)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(user.user_id)
        refresh_token = create_refresh_token(user.user_id)

        decoded = decode_refresh_token(refresh_token)

        session = Session(
            user_id=user.user_id,
            jti=decoded["jti"],
            expires_at=datetime.fromtimestamp(decoded["exp"], tz=UTC),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )

        db.add(session)
        await db.commit()
        response.set_cookie(
            "refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24 * 30,
            path="/",
        )
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def refresh_service(db, request, response):
    try:
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        payload = decode_refresh_token(refresh_token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        session = await get_session_by_jti(db, jti)

        if not session:
            raise HTTPException(status_code=401, detail="Session not found")
        if session.is_revoked:
            await revoke_all_user_sessions(db, user_id)
            raise HTTPException(
                status_code=401, detail="Token reuse detected. All sessions revoked."
            )
        await revoke_session(db, jti)

        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        new_payload = decode_refresh_token(new_refresh_token)

        new_session = Session(
            user_id=user_id,
            jti=new_payload["jti"],
            created_at=datetime.now(UTC),
            expires_at=datetime.fromtimestamp(new_payload["exp"], tz=UTC),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            is_revoked=False,
        )

        await create_session(db, new_session)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24 * 30,
            path="/",
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def logout_service(db, request, response):
    try:
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        payload = decode_refresh_token(refresh_token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        jti = payload.get("jti")

        session = await get_session_by_jti(db, jti)

        if not session:
            response.delete_cookie("refresh_token", path="/")
            return {"message": "Already logged out"}

        if not session.is_revoked:
            await revoke_session(db, jti)

        response.delete_cookie(
            key="refresh_token",
            path="/",
        )

        return {"message": "Logged out successfully"}
    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def forgot_password_request_service(db, email: str):
    try:
        user = await get_user_by_email(db, email)

        if not user:
            raise HTTPException(status_code=404, detail="No user found")

        otp = str(random.randint(100000, 999999))

        set_otp(email, otp)

        print(f"OTP for {email} is {otp}")

        return {"message": f"You OTP is {otp}. Email will be sent."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def forgot_password_verify_service(
    db,
    email: str,
    otp: str,
    new_password: str,
):
    valid = verify_otp(email, otp)

    if not valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    await update_user_password_by_email(db, email, new_password)

    return {"message": "Password updated successfully"}
