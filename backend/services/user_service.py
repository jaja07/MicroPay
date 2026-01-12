from sqlmodel import Session
from uuid import UUID
from passlib.context import CryptContext
from backend.models.user import User
from backend.repositories.user_repository import UserRepository


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
        self.session = session

    def hash_password(self, password: str) -> str:
        """Hache un mot de passe avec bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie qu'un mot de passe correspond à son hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, email: str, password: str) -> User:
        """
        Crée un nouvel utilisateur avec validation.
        
        Raises:
            ValueError: Si l'email existe déjà ou est invalide.
        """
        # Vérifier que l'email n'existe pas déjà
        if self.repository.exists(email):
            raise ValueError(f"Un utilisateur avec l'email {email} existe déjà")
        
        # Valider l'email (simple validation)
        if "@" not in email or "." not in email:
            raise ValueError("Email invalide")
        
        # Hacher le mot de passe
        hashed_password = self.hash_password(password)
        
        # Créer l'utilisateur
        user = User(
            email=email,
            hashed_password=hashed_password
        )
        
        return self.repository.create(user)

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
