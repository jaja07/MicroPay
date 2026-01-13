from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

def get_utc_now():
    return datetime.now(timezone.utc)

# Définition de l'Enum pour le champ 'status'
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
    status: RechargeStatus = Field(nullable=False)
    date: datetime = Field(default_factory=get_utc_now)
    provider_reference: str = Field(nullable=False)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "amount_eur": 50.0,
                "amount_usdc": 58.28,
                "units_granted": 5000.0,
                "payment_provider": "Stripe",
                "status": "completed",
                "date": "2023-10-27T14:30:00",
                "provider_reference": "ref_123456789"
            }
        }