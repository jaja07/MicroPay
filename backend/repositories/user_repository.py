from sqlmodel import Session, select
from uuid import UUID
from backend.models.user_entity import User


class UserRepository:
    """
    Repository pour gérer les opérations CRUD sur la table users.
    Encapsule tous les accès à la base de données pour l'entité User.
    """

    def __init__(self, session: Session):
        """Initialise le repository avec une session SQLModel."""
        self.session = session

    def create(self, user: User, commit: bool = True) -> User:
            """
            Crée un nouvel utilisateur. 
            Si commit=False, l'objet est ajouté à la session et 'flushé' 
            pour générer son ID, mais la transaction reste ouverte.
            """
            self.session.add(user)
            
            if commit:
                self.session.commit()
                self.session.refresh(user)
            else:
                # flush() synchronise l'objet avec la base (génère l'ID UUID)
                # sans terminer la transaction (pas de commit).
                self.session.flush()
                
            return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        statement = select(User).where(User.id == user_id)
        return self.session.exec(statement).first()

    def get_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_all(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste de tous les utilisateurs avec pagination."""
        statement = select(User).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def update(self, user_id: UUID, user_update: dict) -> User | None:
        """Met à jour un utilisateur avec les données fournies."""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in user_update.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: UUID) -> bool:
        """Supprime un utilisateur par son ID."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True

    def exists(self, email: str) -> bool:
        """Vérifie si un utilisateur existe avec cet email."""
        return self.get_by_email(email) is not None
