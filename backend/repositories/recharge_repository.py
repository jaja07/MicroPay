from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
#from datetime import datetime, timezone
from backend.models.recharge_entity import Recharges, RechargeStatus
 

class RechargeRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, recharge: Recharges) -> Recharges:
        """Crée une nouvelle recharge en base de données."""
        self.session.add(recharge)
        self.session.commit()
        self.session.refresh(recharge)
        return recharge

    def get_by_id(self, recharge_id: UUID) -> Optional[Recharges]:
        """Récupère une recharge par son ID unique."""
        statement = select(Recharges).where(Recharges.id == recharge_id)
        return self.session.exec(statement).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Recharges]:
        """Récupère toutes les recharges avec pagination."""
        statement = select(Recharges).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def get_by_user_id(self, user_id: UUID) -> List[Recharges]:
        """
        Récupère toutes les recharges liées à un utilisateur spécifique.
        C'est la méthode clé pour ta relation 1..* (User -> Recharges).
        """
        statement = select(Recharges).where(Recharges.user_id == user_id)
        return self.session.exec(statement).all()

    def get_by_status(self, status: RechargeStatus) -> List[Recharges]:
        """Récupère les recharges filtrées par statut (ex: pending, completed)."""
        statement = select(Recharges).where(Recharges.status == status)
        return self.session.exec(statement).all()

    def update_status(self, recharge_id: UUID, new_status: RechargeStatus) -> Optional[Recharges]:
        """Met à jour uniquement le statut d'une recharge."""
        recharge = self.get_by_id(recharge_id)
        if not recharge:
            return None
        
        recharge.status = new_status
        self.session.add(recharge)
        self.session.commit()
        self.session.refresh(recharge)
        return recharge

    def update(self, recharge_id: UUID, update_data: dict) -> Optional[Recharges]:
        """Met à jour une recharge avec un dictionnaire de données partiel."""
        recharge = self.get_by_id(recharge_id)
        if not recharge:
            return None

        for key, value in update_data.items():
            # On vérifie que l'attribut existe pour éviter les erreurs
            if hasattr(recharge, key) and value is not None:
                setattr(recharge, key, value)

        self.session.add(recharge)
        self.session.commit()
        self.session.refresh(recharge)
        return recharge

    def delete(self, recharge_id: UUID) -> bool:
        """Supprime une recharge."""
        recharge = self.get_by_id(recharge_id)
        if not recharge:
            return False
        
        self.session.delete(recharge)
        self.session.commit()
        return True