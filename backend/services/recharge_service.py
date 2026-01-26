# backend/services/recharge_service.py
import stripe
from sqlmodel import Session
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException
import os
from backend.models.recharge_entity import Recharges, RechargeStatus
from backend.repositories.recharge_repository import RechargeRepository
from backend.repositories.inventory_repository import InventoryRepository
from backend.services.pricing_service import PricingService
from backend.services.treasury_service import TreasuryService

class RechargeService:
    def __init__(self, session: Session):
        self.repo = RechargeRepository(session)
        self.inventory = InventoryRepository(session)
        self.pricing = PricingService()
        self.treasury = TreasuryService()
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    def init_payment_by_units(self, user_id: UUID, units: int):
        if units < 1:
            raise HTTPException(status_code=400, detail="Minimum 1 unité.")

        # 1. OBTENIR LE DEVIS (Prix, Frais, TVA)
        quote = self.pricing.calculate_from_units(units)
        usdc_needed = Decimal(str(quote["usdc_value"]))

        # 2. VÉRIFICATION DU STOCK
        physique = self.treasury.get_master_balance_usdc()
        reserve = self.inventory.get_total_reserved_amount()
        
        # Marge de sécurité de 0.1 USDC
        if (physique - reserve) < (usdc_needed + Decimal("0.1")):
            raise HTTPException(status_code=409, detail="Rupture de stock temporaire.")

        # 3. SAUVEGARDE EN BDD
        recharge = Recharges(
            user_id=user_id,
            status=RechargeStatus.PENDING,
            stripe_payment_intent_id="PENDING",
            
            # Données financières calculées
            amount_base_eur=quote["base_eur"],     
            units_granted=quote["units"],          
            amount_usdc_value=quote["usdc_value"], 
            service_fee_eur=quote["fees_eur"],
            stripe_fee_eur=quote["stripe_fee_eur"],
            vat_amount_eur=quote["vat_eur"],
            total_paid_eur=quote["total_to_pay"]   
        )
        saved_recharge = self.repo.create(recharge)

        # 4. RÉSERVATION DU STOCK
        self.inventory.create_reservation(float(usdc_needed), saved_recharge.id)

        # 5. CRÉATION INTENT STRIPE
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(round(quote["total_to_pay"] * 100)), # Montant TTC en centimes
                currency="eur",
                automatic_payment_methods={"enabled": True},
                metadata={
                    "recharge_id": str(saved_recharge.id),
                    "user_id": str(user_id)
                }
            )
            
            self.repo.update(saved_recharge.id, {"stripe_payment_intent_id": intent.id})
            
            # 6. Réponse API
            recharge_read_data = {
                "id": saved_recharge.id,
                "user_id": saved_recharge.user_id,
                "status": saved_recharge.status,
                "created_at": saved_recharge.created_at,                
                "units_granted": int(saved_recharge.units_granted),    
                "amount_usdc_value": float(saved_recharge.amount_usdc_value),
                "amount_base_eur": float(saved_recharge.amount_base_eur),
                "service_fee_eur": float(saved_recharge.service_fee_eur),
                "vat_amount_eur": float(saved_recharge.vat_amount_eur),
                "stripe_fee_eur": float(saved_recharge.stripe_fee_eur),
                "total_paid_eur": float(saved_recharge.total_paid_eur),
                "payment_provider": "stripe",
                "provider_reference": intent.id,
            }

            return {
                "client_secret": intent.client_secret,
                "recharge": recharge_read_data
            }

        except Exception as e:
            self.inventory.delete_reservation_by_recharge_id(saved_recharge.id)
            self.repo.update(saved_recharge.id, {"status": RechargeStatus.FAILED})
            raise e