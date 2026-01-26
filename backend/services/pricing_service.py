# backend/services/pricing_service.py
from decimal import Decimal, ROUND_HALF_UP

class PricingService:
    # CONFIGURATION
    EUR_PER_USDC = Decimal("1.00")
    UNITS_PER_USDC = Decimal("10") # 1 USDC = 10 Crédits
    
    FEE_PERCENT = Decimal("0.03") # 3% de frais de service
    VAT_RATE = Decimal("0.20")    # 20% de TVA

    # --- CONFIG STRIPE ---
    STRIPE_RATE = Decimal("0.015")  # 1.5%
    STRIPE_FIXED = Decimal("0.25")  # 0.25€

    @classmethod
    def calculate_from_units(cls, units: int) -> dict:
        """
        Calcule le prix à partir du nombre d'unités demandées.
        """
        # 1. Conversion : Unités -> USDC -> EUR Base
        usdc_value = Decimal(units) / cls.UNITS_PER_USDC
        base_eur = usdc_value * cls.EUR_PER_USDC
        
        return cls._calculate_details(base_eur, usdc_value, units)

    @classmethod
    def _calculate_details(cls, base_eur: Decimal, usdc_value: Decimal, units: int) -> dict:
        """
        Logique centralisée des taxes.
        """
        # 2. Calcul des Frais de Service (3%)
        fees = base_eur * cls.FEE_PERCENT
        fees = fees.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # 3. Calcul de la TVA (UNIQUEMENT SUR LES FRAIS)
        # Ex: Si frais = 3.00€ -> TVA = 0.60€
        vat = fees * cls.VAT_RATE
        vat = vat.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Le Net que tu veux recevoir (Base + Tes Frais + Ta TVA)
        net_needed = base_eur + fees + vat

        # 4. CALCUL STRIPE (Formule inversée)
        # On calcule le Total pour que : Total - FraisStripe = NetNeeded
        total_to_pay = (net_needed + cls.STRIPE_FIXED) / (Decimal("1.00") - cls.STRIPE_RATE)
        total_to_pay = total_to_pay.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 5. On isole le montant Stripe pour l'info
        stripe_fee = total_to_pay - net_needed
        

        return {
            "base_eur": float(base_eur),
            "units": int(units),
            "usdc_value": float(usdc_value),
            "fees_eur": float(fees),
            "vat_eur": float(vat),
            "stripe_fee_eur": float(stripe_fee),
            "total_to_pay": float(total_to_pay)
        }