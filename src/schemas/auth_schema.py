from datetime import datetime

from pydantic import BaseModel, EmailStr


class SignupSchema(BaseModel):
    name: str
    email: EmailStr
    contact_no: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    contact_no: str
    role: str
    status: str
    created_at: datetime


class SignupResponse(BaseModel):
    message: str
    user_id: str
    user_name: str
    email: str
    role: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordVerify(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class RevokedToken(BaseModel):
    id: str
    jti: str
