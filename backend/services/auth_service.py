from typing import Annotated
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging, os, random, string, redis, jwt
from ssl import create_default_context
from email.mime.text import MIMEText
from smtplib import SMTP
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
from backend.schema.auth import MailBody
from sqlmodel import Session
from backend.repositories.user_repository import UserRepository
from backend.core.config import settings, make_mail_data_template

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

class AuthService:
    def __init__(self, session: Session):
        self.repository = UserRepository(session)

    def get_password_hash(self, password: str) -> str:
            return password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return password_hash.verify(plain_password, hashed_password)

    #Todo: A supprimer
    def decode_token(self, token: str) -> str:
        """Décode le token et retourne le 'sub' (email)."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise InvalidTokenError
            return email
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalide")

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
        
    def generate_otp(self, length: int = 6) -> str:
        """Génère un code OTP aléatoire."""
        return ''.join(random.choices(string.digits, k=length))

    def send_mail(self, data: dict | None = None):
        try:
            logger.info(f"Début envoi email : {data}")
            msg = MailBody(**data)
            message = MIMEText(msg.body, "html")
            message["From"] = settings.FROM_MAIL
            message["To"] = msg.to
            message["Subject"] = msg.subject

            ctx = create_default_context()

            with SMTP(settings.MAIL_HOST, settings.MAIL_PORT) as server:
                
                server.ehlo()
                server.starttls(context=ctx)
                server.ehlo()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.send_message(message)
                logger.info(f"Email envoyé avec succès à {msg.to}")
            
            return {"status": 200, "errors": None}
        
        except Exception as e:
            logger.error(f"Erreur SMTP : {str(e)}", exc_info=True)
            return {"status": 500, "errors": str(e)}
        
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
            
            mail_data = make_mail_data_template(email, otp)
            self.send_mail(mail_data)
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