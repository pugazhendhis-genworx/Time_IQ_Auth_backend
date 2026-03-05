from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.api.rest.dependencies import get_pg_db
from src.core.services.auth_services import (
    forgot_password_request_service,
    forgot_password_verify_service,
    login_service,
    logout_service,
    refresh_service,
    signup_service,
    validate_user_service,
)
from src.schemas.auth_schema import (
    ForgotPasswordRequest,
    ForgotPasswordVerify,
    SignupResponse,
    SignupSchema,
    TokenResponse,
    ValidateResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupSchema, db=Depends(get_pg_db)):
    result = await signup_service(db, payload)
    return {
        "message": "User Signed Up successfully. Login to continue.",
        "user_id": result.user_id,
        "user_name": result.name,
        "email": result.email,
        "role": "Admin",
    }


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_pg_db),
):
    result = await login_service(
        db,
        request,
        response,
        form_data.username,
        form_data.password,
    )
    return result


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db=Depends(get_pg_db)):
    return await refresh_service(db, request, response)


@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db=Depends(get_pg_db),
):
    return await logout_service(db, request, response)


@auth_router.post("/forgot_password/request")
async def forgot_password_request(
    data: ForgotPasswordRequest,
    db=Depends(get_pg_db),
):
    return await forgot_password_request_service(db, data.email)


@auth_router.post("/forgot_password/verify")
async def forgot_password_verify(
    data: ForgotPasswordVerify,
    db=Depends(get_pg_db),
):
    return await forgot_password_verify_service(
        db,
        data.email,
        data.otp,
        data.new_password,
    )


@auth_router.get("/validate", response_model=ValidateResponse)
async def get_user_credentials(request: Request, db=Depends(get_pg_db)):
    return await validate_user_service(db, request)
