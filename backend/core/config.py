from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

def make_mail_data_template(email: str, otp: str) -> dict:
    return {
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

class Settings(BaseSettings):
    # --- Database Configuration ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5434
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: SecretStr

    @property
    def database_url_computed(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # --- Circle API Configuration ---
    CIRCLE_API_KEY: SecretStr
    WALLET_SET_ID: str
    HEX_ENCODED_ENTITY_SECRET: SecretStr
    MASTER_WALLET_ID: str = Field(..., validation_alias="CIRCLE_MASTER_WALLET_ID")
    CIRCLE_BASE_URL: str = "https://api.circle.com/v1"
    USDC_TOKEN_ID: str = Field(..., validation_alias="CIRCLE_USDC_TOKEN_ID")
    GAS_TOKEN_SYMBOL: str = Field("USDC-TESTNET", validation_alias="CIRCLE_GAS_TOKEN_SYMBOL")
    MIN_GAS_THRESHOLD: float = Field(1.0, validation_alias="CIRCLE_MIN_GAS_THRESHOLD")
    
    # --- JWT Configuration ---
    SECRET_KEY: SecretStr = Field(..., validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: float = 60
    
    # --- Email Configuration ---
    MAIL_HOST: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_PORT: int = 587
    FROM_MAIL: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        extra="ignore"
    )

settings = Settings()