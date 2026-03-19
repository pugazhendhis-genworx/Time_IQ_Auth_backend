"""
OTP Store module.

This module implements an in-memory OTP (One-Time Password) store using a standard
Python dictionary. 

**Design Limitations & Notes:**
- Reboots/restarts of the FastAPI application will completely erase all pending OTPs.
- This approach is not suitable for horizontal scaling (multi-instance deployments) 
  unless sticky sessions are used, because instances do not share the `otp_store` state.
- For production multi-instance use cases, consider migrating to Redis or a database table.
"""
from datetime import UTC, datetime, timedelta

otp_store = {}


def set_otp(email: str, otp: str, expiry_minutes: int = 10):
    otp_store[email] = {
        "otp": otp,
        "expires_at": datetime.now(UTC) + timedelta(minutes=expiry_minutes),
    }


def verify_otp(email: str, otp: str):
    record = otp_store.get(email)

    if not record:
        return False

    if record["expires_at"] < datetime.now(UTC):
        otp_store.pop(email, None)
        return False

    if record["otp"] != otp:
        return False

    otp_store.pop(email, None)
    return True
