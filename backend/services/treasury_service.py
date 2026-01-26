# backend/services/treasury_service.py
import uuid
import os
from decimal import Decimal
from backend.services.circle_service import CircleService

class TreasuryService:
    """
    Gère le Master Wallet sur ARC-TESTNET.
    Spécificité ARC : Le Gas se paie en USDC.
    """
    def __init__(self):
        self.connector = CircleService()
        self.master_wallet_id = os.getenv("CIRCLE_MASTER_WALLET_ID")
        self.usdc_token_id = os.getenv("CIRCLE_USDC_TOKEN_ID")

    def get_master_balance_usdc(self) -> Decimal:
        """Récupère le solde USDC disponible"""
        endpoint = f"/w3s/wallets/{self.master_wallet_id}/balances"
        data = self.connector.get(endpoint)
        balances = data.get("data", {}).get("tokenBalances", [])
        
        for b in balances:
            if b.get("token", {}).get("id") == self.usdc_token_id:
                return Decimal(b.get("amount", "0"))
        return Decimal("0.00")

    def execute_transfer_to_user(self, user_wallet_address: str, amount: float) -> str:
        # Vérification du solde (Marchandise + Gas)
        balance = self.get_master_balance_usdc()
        if balance < Decimal(str(amount)) + Decimal("0.1"):
            print(f"Solde bas ({balance}) pour envoi de {amount}")

        # Envoi
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "entitySecretCiphertext": self.connector.encrypt_entity_secret(),
            "amounts": [str(amount)],
            "feeLevel": "MEDIUM",
            "tokenId": self.usdc_token_id,
            "walletId": self.master_wallet_id,
            "destinationAddress": user_wallet_address,
            "refId": f"payout_{uuid.uuid4()}"
        }
        
        response = self.connector.post("/w3s/developer/transactions/transfer", payload)
        return response.get("data", {}).get("id")