from dotenv import load_dotenv
import os
import uuid
from pathlib import Path
from circle.web3 import developer_controlled_wallets
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def generate_ciphertext(public_key_pem: str, entity_secret_hex: str) -> str:
    """Chiffre l'Entity Secret avec la clé publique de Circle (RSA-OAEP)"""
    entity_secret = bytes.fromhex(entity_secret_hex)
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    
    ciphertext = public_key.encrypt(
        entity_secret,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode()

def create_wallet():
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    api_key = os.getenv("CIRCLE_API_KEY")
    entity_secret = os.getenv("HEX_ENCODED_ENTITY_SECRET")
    wallet_set_id = os.getenv("WALLET_SET_ID")

    # 2. Configuration initiale du client (sans ciphertext pour l'instant)
    configuration = developer_controlled_wallets.Configuration(
        host="https://api.circle.com",
        api_key=api_key
    )

    with developer_controlled_wallets.ApiClient(configuration) as api_client:
        try:
            # --- ÉTAPE A : Récupérer la Clé Publique ---
            print("Récupération de la clé publique Circle...")
            public_key_api = developer_controlled_wallets.PublicKeyApi(api_client)
            pk_response = public_key_api.get_public_key()
            circle_pub_key = pk_response.data.public_key

            # --- ÉTAPE B : Générer le Ciphertext ---
            print("Génération du ciphertext...")
            ciphertext = generate_ciphertext(circle_pub_key, entity_secret)
            
            # Appliquer le ciphertext à la configuration pour les appels suivants
            configuration.entity_secret_ciphertext = ciphertext

            # --- ÉTAPE C : Créer les Wallets ---
            print(f"Création de wallets pour le Wallet Set: {wallet_set_id}...")
            wallets_api = developer_controlled_wallets.WalletsApi(api_client)
            
            # Utilisation d'une Idempotency Key (Bonne pratique C# / Production)
            idempotency_key = str(uuid.uuid4())

            request = developer_controlled_wallets.CreateWalletRequest.from_dict({
                "idempotencyKey": idempotency_key,
                "accountType": 'SCA',
                "blockchains": ['MATIC-AMOY'],
                "count": 2,
                "walletSetId": wallet_set_id
            })

            response = wallets_api.create_wallet(request)
            
            print("\n✅ Succès ! Wallets créés :")
            for wallet in response.data.wallets:
                print(f"- ID: {wallet.id}")
                print(f"  Adresse: {wallet.address}")
                print(f"  Blockchain: {wallet.blockchain}")

        except developer_controlled_wallets.ApiException as e:
            print(f"\n❌ Erreur API Circle : {e}")
        except Exception as e:
            print(f"\n❌ Erreur inattendue : {e}")

if __name__ == "__main__":
    create_wallet()