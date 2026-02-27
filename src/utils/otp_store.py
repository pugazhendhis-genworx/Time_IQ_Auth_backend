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
