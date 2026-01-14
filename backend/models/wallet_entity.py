from __future__ import annotations

from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user_entity import User


class Wallet(SQLModel, table=True):
    """
    Modèle représentant un portefeuille Circle lié à un utilisateur.
    """
    __tablename__ = "wallets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    circle_wallet_id: str = Field(max_length=255, unique=True, index=True)
    address: str = Field(max_length=255)
    blockchain: str = Field(max_length=50)
    account_type: str = Field(default="SCA", max_length=20)
    state: str = Field(default="active", max_length=20)
    wallet_set_id: str = Field(max_length=255)
    user: User | None = Relationship(back_populates="user")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "circle_wallet_id": "cir_wallet_abc123",
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "blockchain": "POLYGON-AMOY",
                "account_type": "SCA",
                "state": "active",
                "wallet_set_id": "set_xyz789"
            }
        }
