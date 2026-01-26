# backend/routers/webhook.py
import stripe
import os
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlmodel import Session
from uuid import UUID

from backend.db.session import get_session
from backend.models.recharge_entity import RechargeStatus
from backend.repositories.recharge_repository import RechargeRepository
from backend.repositories.inventory_repository import InventoryRepository
from backend.services.treasury_service import TreasuryService 
from backend.repositories.wallet_repository import WalletRepository

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/payment")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None),
    session: Session = Depends(get_session)
):

    print("\n🔥 >>> ALERTE : UNE REQUÊTE ARRIVE SUR /webhooks/payment ! <<<\n")
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

# --- AIGUILLAGE DES ÉVÉNEMENTS ---

    # CAS 1 : Succès
    if event['type'] == 'payment_intent.succeeded':
        print("\n Webhook: Paiement RÉUSSI. Traitement...")
        await handle_payment_success(event['data']['object'], session)

    # CAS 2 : Échec (Celui qu'on ajoute)
    elif event['type'] == 'payment_intent.payment_failed':
        print("\n Webhook: Paiement ÉCHOUÉ. Nettoyage...")
        await handle_payment_failure(event['data']['object'], session)

    return {"status": "success"}

async def handle_payment_success(payment_intent: dict, session: Session):
    """
    C'est ici que s'effectue le transfert des fonds équivalents.
    """
    print(f"🧐 METADATA REÇUES DE STRIPE : {payment_intent.get('metadata')}")

    recharge_id = payment_intent['metadata'].get('recharge_id')
    user_id = payment_intent['metadata'].get('user_id')
    
    if not recharge_id:
        return

    # 1. Initialisation des services
    repo = RechargeRepository(session)
    inv_repo = InventoryRepository(session)
    treasury = TreasuryService() # <--- Notre service connecté à Arc Testnet
    wallet_repo = WalletRepository(session)

    # 2. Récupération de la commande
    recharge = repo.get_by_id(UUID(recharge_id))
    
    if not recharge or recharge.status == RechargeStatus.COMPLETED:
        # Déjà traité ou introuvable
        return

    print(f"Paiement de {recharge.amount_base_eur}€ validé. Transfert des fonds...")

# 2. RÉCUPÉRATION DE L'ADRESSE UTILISATEUR (La partie demandée)
    try:
        user_uuid = UUID(user_id)
        user_wallet = wallet_repo.get_by_user_id(user_uuid)
        
        if not user_wallet:
            print(f"ERREUR CRITIQUE : Aucun wallet trouvé pour l'user {user_id}")
            # On ne peut pas livrer les fonds si l'user n'a pas de wallet
            # TODO: Créer un ticket support ou marquer la recharge en "MANUAL_CHECK_NEEDED"
            return
            
        destination_address = user_wallet.address # L'adresse 0x... stockée en BDD
        print(f"Wallet trouvé : {destination_address}")

    except Exception as e:
        print(f"Erreur lors de la récupération du wallet : {e}")
        return

    try:
        # 4. LE MOMENT CLÉ : TRANSFERT DES FONDS ÉQUIVALENTS
        # On utilise 'amount_usdc_value' qui a été calculé lors de l'init_payment
        # C'est ici qu'on transforme les Euros payés en USDC livrés
        tx_id = treasury.execute_transfer_to_user(
            destination_address,
            float(recharge.amount_usdc_value) 
        )
        
        print(f" Virement USDC effectué ! TX: {tx_id}")
        
        # 5. Validation de la commande
        repo.update(recharge.id, {"status": RechargeStatus.COMPLETED})

    except Exception as e:
        print(f"Erreur critique lors du virement : {e}")
        # On ne valide PAS la recharge pour pouvoir réessayer plus tard
        return

    # 6. Libération du stock réservé
    inv_repo.delete_reservation_by_recharge_id(recharge.id)


# --- NOUVELLE FONCTION ÉCHEC ---
async def handle_payment_failure(payment_intent: dict, session: Session):
    """
    Libère le stock et marque la commande comme échouée.
    """
    recharge_id = payment_intent['metadata'].get('recharge_id')
    
    if not recharge_id:
        print("Webhook Failed reçu sans ID.")
        return

    print(f"Traitement de l'échec pour la recharge : {recharge_id}")

    # 1. Init des repos
    repo = RechargeRepository(session)
    inv_repo = InventoryRepository(session)

    try:
        uuid_recharge = UUID(recharge_id)
        
        # 2. Mise à jour statut -> FAILED
        repo.update(uuid_recharge, {"status": RechargeStatus.FAILED})
        print("   -> Statut mis à jour : FAILED")

        # 3. Libération immédiate du stock
        # On utilise la méthode 'secure' qu'on a codée tout à l'heure
        inv_repo.delete_reservation_by_recharge_id(uuid_recharge)
        print("   -> Stock libéré immédiatement.")

    except Exception as e:
        print(f"Erreur lors du nettoyage de l'échec : {e}")