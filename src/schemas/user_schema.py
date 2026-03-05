from datetime import datetime

from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    contact_no: str
    password: str
    role_name: str


class UserOut(BaseModel):
    user_id: str
    name: str
    email: str
    contact_no: str | None = None
    status: str
    role: str | None = None
    created_at: datetime | None = None


class RoleOut(BaseModel):
    role_id: str
    name: str
