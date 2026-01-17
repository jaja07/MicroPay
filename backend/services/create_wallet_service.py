from dotenv import load_dotenv
import os
import uuid
import requests
from pathlib import Path
from circle.web3 import developer_controlled_wallets
from circle.web3.developer_controlled_wallets import WalletsDataWalletsInner
import base64
import codecs
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

def get_public_key(api_key: str) -> str:
    """Récupère la clé publique de Circle via leur API."""
    url = "https://api.circle.com/v1/w3s/config/entity/publicKey"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json().get("data", {})
    public_key = data.get("publicKey")
    if not public_key:
        raise ValueError("La réponse Circle ne contient pas de champ 'publicKey'.")
    return public_key


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante: {name}")
    return value

def generate_ciphertext(public_key_string: str, hex_encoded_entity_secret: str) -> str:
    """Chiffre l'Entity Secret avec la clé publique de Circle (RSA-OAEP)"""
    entity_secret = bytes.fromhex(hex_encoded_entity_secret)

    if len(entity_secret) != 32:
        print("invalid entity secret")
        exit(1)

    public_key = RSA.importKey(public_key_string)

    # encrypt data by the public key
    cipher_rsa = PKCS1_OAEP.new(key=public_key, hashAlgo=SHA256)
    encrypted_data = cipher_rsa.encrypt(entity_secret)

    # encode to base64
    encrypted_data_base64 = base64.b64encode(encrypted_data)

    print("Hex encoded entity secret:", codecs.encode(entity_secret, 'hex').decode())
    print("Entity secret ciphertext:", encrypted_data_base64.decode())
    return encrypted_data_base64.decode()

def create_wallet(idempotency_key: str, user_name: str) -> list[dict] | None:
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    api_key = require_env("CIRCLE_API_KEY")
    entity_secret = require_env("HEX_ENCODED_ENTITY_SECRET")
    wallet_set_id = require_env("WALLET_SET_ID")
    # Utilise l'URL Sandbox si tu as une clé de test
    base_url = "https://api-sandbox.circle.com" 

    # 1. Récupération de la clé publique
    public_key = get_public_key(api_key)

    # 2. Génération du ciphertext
    ciphertext = generate_ciphertext(public_key, entity_secret)
    
    #url = f"{base_url}/v1/w3s/developer/wallets"
    url = 'https://api.circle.com/v1/w3s/developer/wallets'

    payload = {
        "idempotencyKey": idempotency_key,
        "blockchains": ["ARC-TESTNET"],
        "entitySecretCiphertext": ciphertext,
        "walletSetId": wallet_set_id,
        "accountType": "SCA",
        "count": 1,
        "metadata": [
            {
                "name": f"{user_name} Wallet",
                "refId": f"user_{idempotency_key[:8]}"
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}", # Vérifie si TEST_API_KEY est déjà dans ton .env
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    
    # Debug crucial pour les erreurs 400
    if not response.ok:
        print(f"Erreur Circle ({response.status_code}): {response.text}")
        response.raise_for_status()

    data = response.json().get("data", {})
    return data.get("wallets")


if __name__ == "__main__":
    create_wallet(idempotency_key=str(uuid.uuid4()))