# from __future__ import annotations
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_entity import User

class RechargeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Recharges(SQLModel, table=True):
    __tablename__ = "recharges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")

    amount_eur: float = Field(nullable=False)
    amount_usdc: float = Field(nullable=False)
    units_granted: float = Field(nullable=False)
    payment_provider: str = Field(nullable=False)
    status: RechargeStatus = Field(default=RechargeStatus.PENDING, nullable=False)
    provider_reference: str = Field(nullable=False)

    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relation inverse
    user: Optional["User"] = Relationship(back_populates="recharges")