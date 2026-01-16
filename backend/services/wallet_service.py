import logging
from sqlmodel import Session
from uuid import UUID
from typing import Optional

from backend.models.wallet_entity import Wallet
from backend.repositories.wallet_repository import WalletRepository
from backend.services import create_wallet_service

# Configuration du logger pour suivre les erreurs en production
logger = logging.getLogger(__name__)

class WalletService:
    def __init__(self, session: Session):
        self.repository = WalletRepository(session)
        self.session = session

    def create_wallet(self, user_id: UUID) -> Wallet:
        """
        Gère le workflow de création d'un wallet.
        Inclut la validation, la sécurité Circle et la persistance.
        """
        
        # 1. VALIDATION : Vérifier si l'utilisateur possède déjà un wallet
        # On évite de payer des frais Circle inutiles si l'appel est relancé
        existing_wallet = self.repository.get_by_user_id(user_id)
        if existing_wallet:
            logger.info(f"L'utilisateur {user_id} possède déjà un wallet. Retour de l'existant.")
            return existing_wallet

        try:
            # 2. APPEL CIRCLE : Création physique
            # On passe l'user_id comme clé d'idempotence pour la sécurité Circle
            logger.info(f"Appel à l'API Circle pour l'utilisateur {user_id}...")
            circle_wallets_list = create_wallet_service.create_wallet(idempotency_key=str(user_id))
            
            if not circle_wallets_list:
                raise ValueError("La réponse de Circle est vide.")

            circle_wallet = circle_wallets_list[0]

            # 3. MAPPING : Préparation de l'entité locale
            wallet_entity = Wallet(
                user_id=user_id,
                circle_wallet_id=circle_wallet["id"],
                address=circle_wallet["address"],
                blockchain=circle_wallet["blockchain"],
                account_type=circle_wallet["accountType"],
                state=circle_wallet["state"],
                wallet_set_id=circle_wallet["walletSetId"]
            )

            # 4. PERSISTANCE : Enregistrement en base de données
            logger.info(f"Enregistrement du wallet {circle_wallet['id']} en base de données.")
            return self.repository.create(wallet_entity)

        except Exception as e:
            # 5. GESTION DES ERREURS
            # On logue l'erreur pour le debug sans forcément exposer les détails techniques au client
            logger.error(f"Erreur lors du workflow de création de wallet pour {user_id}: {str(e)}")
            
            # Ici, on pourrait ajouter une logique de "rollback" ou d'alerte
            # car si Circle a créé le wallet mais que la DB a échoué, on a une désynchronisation.
            raise RuntimeError(f"Impossible de finaliser la création du wallet : {str(e)}")