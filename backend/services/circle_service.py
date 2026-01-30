# backend/services/circle_service.py
import uuid, base64, requests
from dotenv import load_dotenv, find_dotenv
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from backend.core.config import Settings


class CircleService:
    """
    Connecteur technique bas niveau vers l'API Circle W3S.
    Gère l'auth, le chiffrement du secret et les requêtes HTTP brutes.
    """

    def __init__(self):
        # load_dotenv(find_dotenv())

        self.api_key = Settings.CIRCLE_API_KEY.get_secret_value()
        self.entity_secret = Settings.HEX_ENCODED_ENTITY_SECRET.get_secret_value()
        self.base_url = Settings.CIRCLE_BASE_URL
        self.wallet_set_id = Settings.WALLET_SET_ID

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        
    # ─────────────────────────────
    # Circle helpers
    # ─────────────────────────────

    def get_public_key(self) -> str:
        """Récupère la clé publique Circle"""
        url = f"{self.base_url}/w3s/config/entity/publicKey"
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()

        public_key = response.json().get("data", {}).get("publicKey")
        if not public_key:
            raise ValueError("Clé publique Circle introuvable")

        return public_key

    def encrypt_entity_secret(self) -> str:
        """Chiffre l’entity secret avec la clé publique Circle"""
        public_key_string = self.get_public_key()
        entity_secret_bytes = bytes.fromhex(self.entity_secret)

        if len(entity_secret_bytes) != 32:
            raise ValueError("Entity secret invalide (doit faire 32 bytes)")

        public_key = RSA.import_key(public_key_string)
        cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
        encrypted = cipher.encrypt(entity_secret_bytes)

        return base64.b64encode(encrypted).decode()
    
    def create_wallet(
        self,
        idempotency_key: str,
        user_name: str
    ) -> list[dict] | None:
    
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        ciphertext = self.encrypt_entity_secret()

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

        response = self.post(
            endpoint="/w3s/developer/wallets",
            payload=payload
        )

        return response.get("data", {}).get("wallets", [])

    # ─────────────────────────────
    # HTTP générique
    # ─────────────────────────────
    
    def get(self, endpoint: str) -> dict:
        """GET générique Circle"""

        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, timeout=15)

        if not response.ok:
            print(f"Erreur Circle GET ({response.status_code}): {response.text}")
            response.raise_for_status()
        
        return response.json()


    def post(self, endpoint: str, payload: dict) -> dict:
        """POST générique Circle"""

        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload, headers=self.headers, timeout=15)

        if not response.ok:
            print(f"Erreur Circle ({response.status_code}): {response.text}")
            response.raise_for_status()

        return response.json()
