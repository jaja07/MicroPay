from __future__ import annotations
from enum import Enum
from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .wallet_entity import Wallet
    from .recharge_entity import Recharges

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    nom: str = Field(nullable=False)
    prenom: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.USER, nullable=False)
    hashed_password: str = Field(nullable=False)
    
    # Utilisation directe de la timezone UTC pour la cohérence
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relations
    # Un utilisateur a UN seul wallet (1-to-1)
    wallet: Optional["Wallet"] = Relationship(back_populates="user")
    # Un utilisateur a PLUSIEURS recharges (1-to-Many)
    recharges: List["Recharges"] = Relationship(back_populates="user")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "nom": "Doe",
                "prenom": "John",
                "role": "user"
            }
        }