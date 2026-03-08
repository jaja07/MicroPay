import logging, redis
from sqlmodel import Session
from uuid import UUID
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from typing import Optional

from backend.core.config import settings
from backend.models.user_entity import User
from backend.schema.user import UserCreateDTO, UserUpdateDTO
from backend.repositories.user_repository import UserRepository
from backend.services.wallet_service import WalletService
from backend.services.auth_service import AuthService
from backend.services.treasury_service import TreasuryService

# Configuration du logger pour suivre les erreurs en production
logger = logging.getLogger(__name__)

# Connexion Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token") # It declares that the URL for obtaining the token is /users/token, which corresponds to the login endpoint defined in user.py.
password_hash = PasswordHash.recommended()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class UserService:
    """
    Service contenant la logique métier pour les utilisateurs.
    Encapsule la validation, le hachage des mots de passe et les règles métier.
    """


    def __init__(self, session: Session):
        self.repository = UserRepository(session)
        self.wallet_service = WalletService(session)
        self.session = session
        self.auth_service = AuthService(session)
        self.treasury = TreasuryService()

    def get_user(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        return self.repository.get_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste de tous les utilisateurs."""
        return self.repository.get_all(skip=skip, limit=limit)

    """Todo: Rendre la fonction async
        Ajouter des outbox pattern ou des tâches de nettoyage (crons) pour vérifier la cohérence entre la base de données et 
        Circle (ex: si un wallet a été créé mais que l'utilisateur n'a pas été validé, ou inversement).""" 
    def create_user(self, user: UserCreateDTO) -> User:
        # 1. Vérification d'unicité
        if self.repository.exists(user.email):
            raise ValueError(f"A user with the email {user.email} already exists")

        # 2. Préparation des données
        hashed_password = self.auth_service.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            nom=user.nom,
            prenom=user.prenom,
            role=user.role,
            hashed_password=hashed_password
        )

        try:
            # ÉTAPE A : Créer l'utilisateur en base (SANS commit)
            # Le repository fait un session.add() et session.flush()
            # Cela génère l'ID (UUID) sans valider la transaction.
            created_user = self.repository.create(db_user, commit=False)

            # ÉTAPE B : Créer le wallet Circle
            # On utilise l'ID généré au-dessus. 
            # Si Circle renvoie une erreur, on saute directement au 'except'.
            self.wallet_service.create_wallet(created_user.id, f"{created_user.nom} {created_user.prenom}")

            # ÉTAPE C : Validation finale
            # Si on arrive ici, l'user et le wallet sont prêts en mémoire/flush.
            # On valide les deux d'un seul coup.
            self.session.commit()
            
            # ÉTAPE D : Rafraîchissement
            # Maintenant que c'est en base, on recharge l'objet pour avoir ses relations
            self.session.refresh(created_user)

            # ÉTAPE E : Envoyer OTP par email
            try:
                self.auth_service.send_otp_email(created_user.email)
                logger.info(f"OTP envoyé automatiquement à {created_user.email}")
            except Exception as otp_error:
                logger.error(f"Erreur envoi OTP après inscription : {str(otp_error)}")
                # On ne lève pas l'erreur car l'utilisateur est déjà créé
            return created_user

        except Exception as e:
            # En cas d'erreur (Circle, DB, ou erreur de code), on annule TOUT.
            # L'utilisateur ne sera pas créé en base s'il n'a pas pu avoir de wallet.
            self.session.rollback()
            # On remonte l'erreur pour que l'API puisse renvoyer le bon code HTTP
            raise e

    def update_user(self, user_id: UUID, user_data: UserUpdateDTO) -> Optional[User]:
        """
        Service pour mettre à jour un utilisateur.
        Orchestre la logique métier avant l'appel au repository.
        """
        update_dict = user_data.model_dump(exclude_unset=True)

        if "password" in update_dict:
            raw_password = update_dict.pop("password")
            update_dict["hashed_password"] = self.auth_service.get_password_hash(raw_password)

        if "email" in update_dict:
            if self.repository.exists(update_dict["email"]):
                raise ValueError(f"A user with the email {update_dict['email']} already exists")

        return self.repository.update(user_id, update_dict)

    def delete_user(self, user_id: UUID) -> bool:
        """Supprime un utilisateur par son ID."""
        return self.repository.delete(user_id)
    

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authentifie un utilisateur avec email et mot de passe.
        Retourne l'objet User si authentifié, sinon None.
        """
        user = self.repository.get_by_email(email)
        if not user:
            return None
        if not self.auth_service.verify_password(password, user.hashed_password):
            return None
        return user
    
    def bill_user_for_tokens(self, user_id: UUID, tokens_consumed: int, model_name: str, cost_usd: float):
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        user_wallet = user.wallet
        if not user_wallet:
            raise Exception("L'utilisateur n'a pas de wallet.")

        # 2. Effectuer le prélèvement sur la blockchain via Circle
        transaction_id = self.treasury.charge_user_wallet(
            user_wallet_id=user_wallet.circle_wallet_id,
            amount=cost_usd
        )

        # 3. Enregistrer la consommation dans ta table token_usage
        # (À implémenter avec un repository dédié pour token_usage)
        # usage_repo.create_usage(...)
        
        return transaction_id