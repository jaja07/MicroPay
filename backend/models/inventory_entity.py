from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

#EXPIRATION_DELAY_MINUTES = 10

def get_expiration_time(minutes=10):
    # La réservation expire après 10 min si pas de paiement
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)

class InventoryReservation(SQLModel, table=True):
    __tablename__ = "inventory_reservations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    amount_usdc: float = Field(description="Montant bloqué")
    recharge_id: UUID = Field(index=True) # Lien vers la tentative d'achat
    expires_at: datetime = Field(default_factory=get_expiration_time, index=True)