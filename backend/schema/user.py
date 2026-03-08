from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from enum import Enum

from .recharge import RechargeRead
from .wallet import WalletReadDTO

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str

class UserReadDTO(UserBase):
    id: UUID
    role: Role
    created_at: datetime
    recharges: list[RechargeRead] = []
    wallet: WalletReadDTO | None = None

    class Config:
        from_attributes = True

class UserCreateDTO(UserBase):
    password: str
    role: Role = Role.USER

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "nom": "DOE",
                "prenom": "John",
                "role": "user",
                "password": "1234",
                "units": 0.0
            }
    }

class UserUpdateDTO(BaseModel):
    email: EmailStr | None = None
    nom: str | None = None
    prenom: str | None = None
    password: str | None = None
    units: float | None = None
    role: Role | None = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "updated@example.com",
                "nom": "Updated",
                "prenom": "User",
                "password": "newpassword123",
                "units": 10.0,
                "role": "user"
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
