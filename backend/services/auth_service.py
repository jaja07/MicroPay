import logging, os
from dotenv import load_dotenv
from backend.schema.auth import MailBody
from ssl import create_default_context
from email.mime.text import MIMEText
from smtplib import SMTP

load_dotenv("backend/.env")
HOST = os.environ.get("MAIL_HOST")
USERNAME = os.environ.get("MAIL_USERNAME")
PASSWORD = os.environ.get("MAIL_PASSWORD")
PORT = os.environ.get("MAIL_PORT", 465)
FROM_MAIL = os.environ.get("FROM_MAIL", USERNAME)
logger = logging.getLogger(__name__)

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