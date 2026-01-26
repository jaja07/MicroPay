# backend/services/user_service.py
import logging
from sqlmodel import Session
from uuid import UUID
from passlib.context import CryptContext
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
import random, string, redis

from backend.models.user_entity import User
from backend.schema.user import UserCreateDTO
from backend.repositories.user_repository import UserRepository
from backend.services.wallet_service import WalletService
from backend.services.auth_service import send_mail

# Configuration du logger pour suivre les erreurs en production
logger = logging.getLogger(__name__)

# Connexion Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


password_hash = PasswordHash.recommended()


class UserService:
    """
    Service contenant la logique métier pour les utilisateurs.
    Encapsule la validation, le hachage des mots de passe et les règles métier.
    """


    def __init__(self, session: Session):
        self.repository = UserRepository(session)
        self.wallet_service = WalletService(session)
        self.session = session

    def get_password_hash(self, password: str) -> str:
        return password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return password_hash.verify(plain_password, hashed_password)
    
        
    def generate_otp(self, length: int = 6) -> str:
        """Génère un code OTP aléatoire."""
        return ''.join(random.choices(string.digits, k=length))

    def send_otp_email(self, email: str) -> bool:
        """Génère un OTP et l'envoie par email (stocké en Redis)."""
        try:
            user = self.repository.get_by_email(email)
            
            if not user:
                logger.warning(f"Tentative OTP pour email inexistant : {email}")
                return False
            
            otp = self.generate_otp()
            
            # Stocker en Redis avec expiration de 5 minutes
            redis_key = f"otp:{email}"
            redis_client.setex(redis_key, 300, otp)  # 300 secondes = 5 minutes
            
            mail_data = {
                "to": email,
                "subject": "Votre code de vérification MicroPay",
                "body": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 20px;
            background-color: #f7f9fc;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .otp-code {{
            font-size: 42px;
            font-weight: bold;
            letter-spacing: 8px;
            text-align: center;
            margin: 30px 0;
            color: #2d3748;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 2px dashed #e2e8f0;
        }}
        .info-box {{
            background: #f0f7ff;
            border-left: 4px solid #4299e1;
            padding: 15px;
            margin: 25px 0;
            border-radius: 0 8px 8px 0;
        }}
        .footer {{
            text-align: center;
            padding: 25px;
            color: #718096;
            font-size: 14px;
            border-top: 1px solid #e2e8f0;
            background: #f8f9fa;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .expiry-note {{
            color: #e53e3e;
            font-weight: 600;
        }}
        .divider {{
            height: 1px;
            background: #e2e8f0;
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo">MicroPay</div>
            <h1 style="margin: 10px 0 0 0; font-weight: 300;">Verification Code</h1>
        </div>
        
        <div class="content">
            <h2 style="color: #2d3748; margin-top: 0;">Secure Verification</h2>
            
            <p>Hello,</p>
            
            <p>You've requested to verify your identity. Please use the following One-Time Password (OTP) to complete your verification:</p>
            
            <div class="otp-code">{otp}</div>
            
            <div class="info-box">
                <p style="margin: 0;">
                    <strong>Important:</strong> This code will expire in <span class="expiry-note">5 minutes</span>.
                    For your security, please do not share this code with anyone.
                </p>
            </div>
            
            <p>If you didn't request this verification code, please ignore this email or contact our support team if you have concerns.</p>
            
            <div class="divider"></div>
            
            <p style="font-size: 14px; color: #718096;">
                <strong>Tip:</strong> Enter this code promptly to avoid expiration. The code is case-sensitive.
            </p>
        </div>
        
        <div class="footer">
            <p style="margin: 0 0 10px 0;">
                <strong>MicroPay Security Team</strong>
            </p>
            <p style="margin: 0; font-size: 13px;">
                This is an automated message. Please do not reply to this email.<br>
                For assistance, contact our support team.
            </p>
        </div>
    </div>
</body>
</html>"""
            }
            send_mail(mail_data)
            logger.info(f"OTP envoyé à {email}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur envoi OTP : {str(e)}", exc_info=True)
            return False

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """Vérifie le code OTP stocké en Redis."""
        try:
            redis_key = f"otp:{email}"
            stored_otp = redis_client.get(redis_key)
            
            if not stored_otp:
                logger.warning(f"OTP expiré ou inexistant pour {email}")
                return False
            
            if stored_otp != otp_code:
                logger.warning(f"OTP invalide pour {email}")
                return False
            
            # Supprimer l'OTP après vérification
            redis_client.delete(redis_key)
            logger.info(f"OTP vérifié avec succès pour {email}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur vérification OTP : {str(e)}", exc_info=True)
            return False


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
