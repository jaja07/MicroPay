import logging, os, random, string, redis, jwt
from dotenv import load_dotenv
from ssl import create_default_context
from email.mime.text import MIMEText
from smtplib import SMTP
from dotenv import load_dotenv
from pathlib import Path
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from backend.schema.auth import MailBody

logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
HOST = os.environ.get("MAIL_HOST")
USERNAME = os.environ.get("MAIL_USERNAME")
PASSWORD = os.environ.get("MAIL_PASSWORD")
PORT = os.environ.get("MAIL_PORT", 465)
FROM_MAIL = os.environ.get("FROM_MAIL", USERNAME)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

def get_password_hash(self, password: str) -> str:
        return password_hash.hash(password)

def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
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

def send_mail(data: dict | None = None):
    try:
        logger.info(f"Début envoi email : {data}")
        msg = MailBody(**data)
        message = MIMEText(msg.body, "html")
        message["From"] = FROM_MAIL
        message["To"] = msg.to
        message["Subject"] = msg.subject

        ctx = create_default_context()

        with SMTP(HOST, PORT) as server:
            
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(USERNAME, PASSWORD)
            server.send_message(message)
            logger.info(f"Email envoyé avec succès à {msg.to}")
        
        return {"status": 200, "errors": None}
    
    except Exception as e:
        logger.error(f"Erreur SMTP : {str(e)}", exc_info=True)
        return {"status": 500, "errors": str(e)}