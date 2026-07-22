from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    organization_name: str
    organization_slug: str
    email: str
    password: str
    display_name: str
    timezone: str = "UTC"
    currency: str = "USD"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    organization_id: str
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserMinimal(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InviteUserRequest(BaseModel):
    email: str
    display_name: str
    role: UserRole = UserRole.viewer


class ChangeRoleRequest(BaseModel):
    role: UserRole


class RegisterResponse(BaseModel):
    organization: dict
    user: dict
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    scope: str
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateRequest(BaseModel):
    name: str
    scope: str = "read"
    expires_at: Optional[datetime] = None


class ApiKeyCreateResponse(BaseModel):
    id: str
    key_prefix: str
    full_key: str
    name: str
    scope: str
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
