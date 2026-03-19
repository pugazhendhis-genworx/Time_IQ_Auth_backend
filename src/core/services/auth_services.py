import random
from datetime import UTC, datetime

from fastapi import HTTPException

from src.core.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
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
    get_user_by_id,
    update_user_password_by_email,
)
from src.observability.logging import logging
from src.utils.otp_store import set_otp, verify_otp
from src.utils.password_hashing import hash_password, verify_password

logger = logging.get_logger(__name__)


async def signup_service(db, user):
    try:
        logger.info(f"Starting signup process for email: {user.email}")
        existing = await get_user_by_email(db, user.email)
        if existing:
            logger.warning(f"Signup failed: Email already registered ({user.email})")
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
        logger.info(f"Signup successful for user: {user.email}")
        return result
    except Exception as e:
        logger.error(f"Error during signup for {user.email}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def login_service(db, request, response, username, password):
    try:
        logger.info(f"Login attempt for user: {username}")
        user = await get_user_by_email(db, username)

        if not user:
            logger.warning(
                f"Login failed - invalid credentials (user not found) for {username}"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user.password):
            logger.warning(f"Login failed - incorrect password for {username}")
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
        logger.info(f"Login successful for user: {username}, session created")
        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception:
        logger.error(f"Login encountered an error for {username}", exc_info=True)


async def refresh_service(db, request, response):
    try:
        logger.info("Processing token refresh request")
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            logger.warning("Token refresh failed: missing refresh token")
            raise HTTPException(status_code=401, detail="Missing refresh token")

        payload = decode_refresh_token(refresh_token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        session = await get_session_by_jti(db, jti)

        if not session:
            logger.warning(f"Token refresh failed: Session not found for jti {jti}")
            raise HTTPException(status_code=401, detail="Session not found")
        if session.is_revoked:
            logger.warning(
                f"Token reuse detected for session {jti}."
                f" Revoking all sessions for user {user_id}"
            )
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

        logger.info(f"Token refresh successful for user {user_id}")
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception:
        logger.error("Refresh token encountered an error", exc_info=True)
        raise


async def logout_service(db, request, response):
    try:
        logger.info("Processing logout request")
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            logger.warning("Logout failed: missing refresh token")
            raise HTTPException(status_code=401, detail="Missing refresh token")

        payload = decode_refresh_token(refresh_token)

        if not payload:
            logger.warning("Logout failed: invalid refresh token")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        jti = payload.get("jti")

        session = await get_session_by_jti(db, jti)

        if not session:
            logger.info("Logout: Session already invalidated or not found")
            response.delete_cookie("refresh_token", path="/")
            return {"message": "Already logged out"}

        if not session.is_revoked:
            await revoke_session(db, jti)

        response.delete_cookie(
            key="refresh_token",
            path="/",
        )

        logger.info(f"Logout successful for session {jti}")
        return {"message": "Logged out successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Logout encountered an error", exc_info=True)


async def forgot_password_request_service(db, email: str):
    try:
        logger.info(f"Forgot password request for email: {email}")
        user = await get_user_by_email(db, email)

        if not user:
            logger.warning(f"Forgot password request failed: No user found for {email}")
            raise HTTPException(status_code=404, detail="No user found")

        otp = str(random.randint(100000, 999999))

        set_otp(email, otp)

        logger.info(f"OTP generated and stored for {email}")
        return {"message": f"Your OTP is {otp}. Email will be sent."}
    except HTTPException:
        raise
    except Exception:
        logger.error(f"Error during forgot password request for {email}", exc_info=True)


async def forgot_password_verify_service(
    db,
    email: str,
    otp: str,
    new_password: str,
):
    try:
        logger.info(f"Verifying OTP for forgot password: {email}")
        valid = verify_otp(email, otp)

        if not valid:
            logger.warning(f"OTP validation failed for {email}")
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP",
            )

        await update_user_password_by_email(db, email, new_password)

        logger.info(f"Password updated successfully for {email}")
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Error during forgot password verification for {email}", exc_info=True
        )
        raise


async def validate_user_service(db, request):
    try:
        logger.info("Validating user access token")
        auth_header = request.headers.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "Token validation failed: Missing or invalid authorization header"
            )
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header",
            )

        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)

        user_id = payload.get("sub")
        if not user_id:
            logger.warning(
                "Token validation failed: Invalid token payload (no sub field)"
            )
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_id": user.user_id,
            "role": user.role.name if user.role else None,
        }
    except HTTPException:
        raise
    except Exception:
        logger.error(f"Error during validating user for {user}", exc_info=True)
        raise
