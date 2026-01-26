# backend/schema/recharges.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from backend.models.recharge_entity import RechargeStatus

# --- 1. INPUT : Ce que le frontend ENVOIE ---
class RechargeInitRequest(BaseModel):
    """
    L'utilisateur choisit combien d'UNITÉS (crédits) il veut.
    Le prix en Euros sera calculé par le Backend.
    """
    units: int = Field(gt=0, description="Nombre de crédits que l'utilisateur veut acheter (ex: 10, 50, 100)")


# --- 2. OUTPUT : Ce que l'API RENVOIE (Lecture complète) ---
# C'est l'objet complet tel qu'il est stocké en BDD après calculs
class RechargeRead(BaseModel):
    id: UUID
    user_id: UUID
    status: RechargeStatus
    created_at: datetime
    
    # Détails de la transaction (Calculés par le Backend)
    units_granted: int          # Combien de crédits il a eu
    amount_base_eur: float      # Le prix des crédits (ex: 50.00)
    service_fee_eur: float      # Les frais ajoutés (ex: 1.50)
    vat_amount_eur: float       # La TVA éventuelle
    stripe_fee_eur: float = 0.0
    total_paid_eur: float       # Ce que Stripe va prélever (ex: 51.50)
    
    # La valeur Crypto correspondante
    amount_usdc_value: float    # Ce qu'on va envoyer sur la blockchain

    class Config:
        from_attributes = True


# --- 3. RÉPONSE D'INITIALISATION ---
class RechargeInitResponse(BaseModel):
    """
    La réponse immédiate quand l'utilisateur clique sur 'Payer'.
    Contient le secret pour Stripe Elements + le récapitulatif de la commande.
    """
    client_secret: str
    recharge: RechargeRead # On renvoie l'objet complet pour afficher le résumé au client