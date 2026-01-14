from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserCreateDTO(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    role: Role
    password: str


class UserReadDTO(BaseModel):
    id: UUID
    email: EmailStr
    nom: str
    prenom: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True # Permet de faire un mapping depuis un objet SQLModel en ce Schema
