from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from backend.models.recharge_entity import RechargeStatus


class RechargeBase(BaseModel):
    amount_eur: float = Field(gt=0, description="Montant en euros")
    payment_provider: str
    provider_reference: str


class RechargeCreate(RechargeBase):
    pass 


class RechargeRead(RechargeBase):
    id: UUID
    user_id: UUID
    amount_eur: float
    amount_usdc: float
    units_granted: float
    payment_provider: str
    status: RechargeStatus = Field(default=RechargeStatus.PENDING, nullable=False)
    provider_reference: str
    date: datetime

    class Config:
        from_attributes = True