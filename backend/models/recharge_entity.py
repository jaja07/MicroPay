# from __future__ import annotations
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

from .user_entity import User

class RechargeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Recharges(SQLModel, table=True):
    __tablename__ = "recharges"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)# Clé étrangère vers Users
    
    # --- Logique Métier (1 Unit = 0.1 USDC) ---
    units_granted: int = Field(description="Nombre d'unités achetées")
    amount_usdc_value: float = Field(description="Valeur sous-jacente en USDC")

    # --- Logique Financière (Facturation) ---
    amount_base_eur: float = Field(description="Prix de base HT")
    service_fee_eur: float = Field(description="Frais de service HT")
    vat_amount_eur: float = Field(description="TVA sur frais")
    stripe_fee_eur: float = Field(default=0.0, description="Frais stripe")
    total_paid_eur: float = Field(description="Total payé par le client TTC")

    # --- Technique ---
    stripe_payment_intent_id: str = Field(index=True)
    status: RechargeStatus = Field(default=RechargeStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relation inverse
    user: Optional[User] = Relationship(back_populates="recharges")