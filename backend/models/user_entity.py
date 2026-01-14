from __future__ import annotations

from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from .wallet_entity import Wallet
from .recharge_entity import Recharges

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    nom: str = Field(nullable=False)
    prenom: str = Field(nullable=False)
    role: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    wallet: Wallet | None = Relationship(back_populates="user")
    recharges: list[Recharges] = Relationship(back_populates="user")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "nom": "Doe",
                "prenom": "John",
                "role": "user",
                "hashed_password": "$2b$12$KIXqH8..."
            }
        }