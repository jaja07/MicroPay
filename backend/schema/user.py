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
                "password": "1234"
            }
    }


