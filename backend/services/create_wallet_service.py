# backend/services/create_wallet_service.py

import uuid
import os
from dotenv import load_dotenv, find_dotenv
from backend.services.circle_service import CircleService


class CreateWalletService:
    def __init__(self):
        load_dotenv(find_dotenv())

        self.circle = CircleService()
        self.wallet_set_id = self._require_env("WALLET_SET_ID")

    @staticmethod
    def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Variable d'environnement manquante: {name}")
        return value

    def create_wallet(
        self,
        idempotency_key: str,
        user_name: str
    ) -> list[dict] | None:
    
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        ciphertext = self.circle.encrypt_entity_secret()

        payload = {
            "idempotencyKey": idempotency_key,
            "blockchains": ["ARC-TESTNET"],
            "entitySecretCiphertext": ciphertext,
            "walletSetId": self.wallet_set_id,
            "accountType": "SCA",
            "count": 1,
            "metadata": [
                {
                    "name": f"{user_name} Wallet",
                    "refId": f"user_{idempotency_key[:8]}"
                }
            ]
        }

        response = self.circle.post(
            endpoint="/w3s/developer/wallets",
            payload=payload
        )

        return response.get("data", {}).get("wallets", [])
