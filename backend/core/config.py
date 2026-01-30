from pydantic import Field, SecretStr, ComputedField
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

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
    MASTER_WALLET_ID: str = Field(..., env="CIRCLE_MASTER_WALLET_ID")
    CIRCLE_BASE_URL: str = "https://api.circle.com/v1"
    USDC_TOKEN_ID: str = Field(..., env="CIRCLE_USDC_TOKEN_ID")
    GAS_TOKEN_SYMBOL: str = Field("USDC-TESTNET", env="CIRCLE_GAS_TOKEN_SYMBOL")
    MIN_GAS_THRESHOLD: float = Field(1.0, env="CIRCLE_MIN_GAS_THRESHOLD")
    
    # --- JWT Configuration ---
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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