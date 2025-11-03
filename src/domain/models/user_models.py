# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import datetime
from enum import Enum

class RoleType(str, Enum):
    administrator = "administrator"
    client = "client"

class UserCreate(BaseModel):
    email: EmailStr
    cnpj_cpf: str
    ip_address: str | None = None
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: RoleType = "client"
    company_id: int | None = None

class UserRead(BaseModel):
    id: int
    email: EmailStr
    cnpj_cpf: str
    ip_address: str | None = None
    full_name: str | None = None
    role: RoleType
    is_active: bool
    status_changed_at: datetime | None = None
    company_id: int | None = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    is_active: bool
    id: int | None

class TokenPayload(BaseModel):
    sub: str  # email
    role: RoleType

class UserUpdateCompany(BaseModel):
    company_id: int

class UserUpdateConfig(BaseModel):
    id: int
    password: str
    full_name: str
