# TimeGuard-auth-backend

TimeGuard authentication backend, built using FastAPI, PostgreSQL, and standard JWT techniques.
It supports registration, login, role management, token refreshing, and forgot-password flows.

## Architecture & Design Decisions

- **FastAPI**: Core async REST framework used for rapid routing and validation.
- **PostgreSQL**: Primary data store for users, sessions, and roles. Accessed via SQLAlchemy.
- **JWT**: Dual-token pattern (short-lived access token, long-lived refresh token). Refresh tokens are managed via HttpOnly cookies format, while access tokens are passed in `Authorization: Bearer` headers.
- **In-Memory OTP Store**: The functionality for password resets utilizes an in-memory Python dictionary to temporarily hold OTPs. 
  - *Limitation*: Because it is stored in application memory (`src/utils/otp_store.py`), it resets completely on app restart/redeployment. It also does not support horizontally scaled multi-instance setups (unless Sticky Sessions are employed) because Instance A won't know the OTP stored on Instance B.
  - *Mitigation*: For production scaling, switch `otp_store` to Redis or a short-lived database table.

## Local Setup & Installation

This project relies on `uv` for minimal dependencies management.

1. Install `uv` if you haven't already.
2. Initialize environment:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```

3. Configure your Environment Variables by copying the example:
   ```bash
   cp .env.example .env
   # Update the database URL and keys inside .env
   ```

4. Run the API locally:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once running, interactive API documentation is easily accessible:
- **Swagger UI**: Visit `http://localhost:8000/docs`. Endpoints are neatly grouped and feature summaries & descriptions.
- **ReDoc**: Alternative UI at `http://localhost:8000/redoc`.
