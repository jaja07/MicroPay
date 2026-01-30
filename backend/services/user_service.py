import os, logging, random, string, redis, jwt
from typing import Annotated
from sqlmodel import Session
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone

from backend.core.config import settings
from backend.models.user_entity import User
from backend.schema.user import UserCreateDTO, TokenData
from backend.repositories.user_repository import UserRepository
from backend.services.wallet_service import WalletService
from backend.services.auth_service import send_mail

# Configuration du logger pour suivre les erreurs en production
logger = logging.getLogger(__name__)

# Connexion Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
password_hash = PasswordHash.recommended()

SECRET_KEY = settings.SECRET_KEY.get_secret_value()
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

    def get_user(self, user_id: UUID) -> User | None:
        """Récupère un utilisateur par son ID."""
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Récupère un utilisateur par son email."""
        return self.repository.get_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """Récupère la liste de tous les utilisateurs."""
        return self.repository.get_all(skip=skip, limit=limit)
    
    def create_user(self, user: UserCreateDTO) -> User:
        # 1. Vérification d'unicité
        if self.repository.exists(user.email):
            raise ValueError(f"Un utilisateur avec l'email {user.email} existe déjà")

        # 2. Préparation des données
        hashed_password = self.get_password_hash(user.password)
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

            # ÉTAPE E : Envoyer OTP par email ✅ NOUVEAU
            try:
                self.send_otp_email(created_user.email)
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
    
    def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
        user = self.get_user_by_email(username)
        if user is None:
            raise credentials_exception
        return user

    def authenticate_user(self, email: str, password: str) -> User | bool:
        """
        Authentifie un utilisateur avec email et mot de passe.
        Retourne l'utilisateur s'il existe et que le mot de passe est correct.
        """
        user = self.repository.get_by_email(email)
        if not user:
            return False
        
        if not self.verify_password(password, user.hashed_password):
            return False
        
        return user