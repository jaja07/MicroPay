from __future__ import annotations
from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID, uuid4
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user_entity import User

class Wallet(SQLModel, table=True):
    __tablename__ = "wallets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Ajout de unique=True pour garantir la relation 1-to-1 au niveau DB
    user_id: UUID = Field(
        foreign_key="users.id", 
        ondelete="CASCADE", 
        unique=True 
    )
    
    circle_wallet_id: str = Field(max_length=255, unique=True, index=True)
    address: str = Field(max_length=255)
    blockchain: str = Field(max_length=50)
    account_type: str = Field(default="SCA", max_length=20)
    state: str = Field(default="active", max_length=20)
    wallet_set_id: str = Field(max_length=255)

    # Correction du back_populates pour pointer vers l'attribut 'wallet' de User
    user: Optional["User"] = Relationship(back_populates="wallet")