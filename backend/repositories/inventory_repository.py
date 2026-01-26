from sqlmodel import Session, select, func, delete
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from backend.models.inventory_entity import InventoryReservation

class InventoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_reservation(self, amount_usdc: float, recharge_id: UUID):
        reservation = InventoryReservation(amount_usdc=amount_usdc, recharge_id=recharge_id)
        self.session.add(reservation)
        self.session.commit()
        return reservation

    def get_total_reserved_amount(self) -> Decimal:
        # Somme des réservations non expirées
        now = datetime.now(timezone.utc)
        statement = select(func.sum(InventoryReservation.amount_usdc)).where(
            InventoryReservation.expires_at > now
        )
        result = self.session.exec(statement).one()
        return Decimal(str(result)) if result else Decimal("0.00")

    def delete_reservation_by_recharge_id(self, recharge_id: UUID):
        statement = delete(InventoryReservation).where(
            InventoryReservation.recharge_id == recharge_id
        )
        self.session.exec(statement)
        self.session.commit()