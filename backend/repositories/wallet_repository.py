from sqlmodel import Session, select
from uuid import UUID
from backend.models.wallet_entity import Wallet

class WalletRepository:
    """
    Repository pour gérer les opérations CRUD sur la table wallets.
    Encapsule tous les accès à la base de données pour l'entité Wallet.
    """

    def __init__(self, session: Session):
        """Initialise le repository avec une session SQLModel."""
        self.session = session

    def create(self, wallet: Wallet) -> Wallet:
        """Crée un nouveau wallet en base de données."""
        self.session.add(wallet)
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

    def get_by_id(self, wallet_id: UUID) -> Wallet | None:
        """Récupère un wallet par son ID."""
        statement = select(Wallet).where(Wallet.id == wallet_id)
        return self.session.exec(statement).first()

    def get_by_user_id(self, user_id: UUID) -> Wallet | None:
        """Récupère un wallet par l'ID de l'utilisateur associé."""
        statement = select(Wallet).where(Wallet.user_id == user_id)
        return self.session.exec(statement).first()

    def update(self, wallet_id: UUID, wallet_update: dict) -> Wallet | None:
        """Met à jour un wallet avec les données fournies."""
        wallet = self.get_by_id(wallet_id)
        if not wallet:
            return None
        
        for key, value in wallet_update.items():
            if hasattr(wallet, key) and value is not None:
                setattr(wallet, key, value)
        
        self.session.add(wallet)
        self.session.commit()
        self.session.refresh(wallet)
        return wallet

    def delete(self, wallet_id: UUID) -> bool:
        """Supprime un wallet par son ID."""
        wallet = self.get_by_id(wallet_id)
        if not wallet:
            return False
        
        self.session.delete(wallet)
        self.session.commit()
        return True