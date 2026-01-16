import logging
from sqlmodel import Session
from uuid import UUID
from passlib.context import CryptContext
from backend.models.user_entity import User
from backend.schema.user import UserCreateDTO
from backend.repositories.user_repository import UserRepository
from backend.services import create_wallet_service
from backend.services.wallet_service import WalletService

# Configuration du logger pour suivre les erreurs en production
logger = logging.getLogger(__name__)

# Configuration du contexte de hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """
    Service contenant la logique métier pour les utilisateurs.
    Encapsule la validation, le hachage des mots de passe et les règles métier.
    """

    def __init__(self, session: Session):
        """Initialise le service avec une session et un repository."""
        self.repository = UserRepository(session)
        self.wallet_service = WalletService(session)
        self.session = session

    def hash_password(self, password: str) -> str:
        """Hache un mot de passe avec bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie qu'un mot de passe correspond à son hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, user: UserCreateDTO) -> User:
        # 1. Vérification d'unicité
        if self.repository.exists(user.email):
            raise ValueError(f"Un utilisateur avec l'email {user.email} existe déjà")

        # 2. Préparation des données
        hashed_password = self.hash_password(user.password)
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
            self.wallet_service.create_wallet(created_user.id)

            # ÉTAPE C : Validation finale
            # Si on arrive ici, l'user et le wallet sont prêts en mémoire/flush.
            # On valide les deux d'un seul coup.
            self.session.commit()
            
            # ÉTAPE D : Rafraîchissement
            # Maintenant que c'est en base, on recharge l'objet pour avoir ses relations
            self.session.refresh(created_user)
            return created_user

        except Exception as e:
            # En cas d'erreur (Circle, DB, ou erreur de code), on annule TOUT.
            # L'utilisateur ne sera pas créé en base s'il n'a pas pu avoir de wallet.
            self.session.rollback()
            # On remonte l'erreur pour que l'API puisse renvoyer le bon code HTTP
            raise e

    def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authentifie un utilisateur avec email et mot de passe.
        Retourne l'utilisateur s'il existe et que le mot de passe est correct.
        """
        user = self.repository.get_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user

    def get_user(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        return self.repository.get_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste de tous les utilisateurs."""
        return self.repository.get_all(skip=skip, limit=limit)

    def update_user(self, user_id: UUID, email: str = None, password: str = None) -> User | None:
        """
        Met à jour un utilisateur.
        Hache le nouveau mot de passe s'il est fourni.
        """
        update_data = {}
        
        if email is not None:
            # Vérifier que le nouvel email n'existe pas
            if email != self.repository.get_by_id(user_id).email:
                if self.repository.exists(email):
                    raise ValueError(f"Un utilisateur avec l'email {email} existe déjà")
            update_data["email"] = email
        
        if password is not None:
            update_data["hashed_password"] = self.hash_password(password)
        
        return self.repository.update(user_id, update_data)

    def delete_user(self, user_id: UUID) -> bool:
        """Supprime un utilisateur par son ID."""
        return self.repository.delete(user_id)
