from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from backend.models.recharge_entity import RechargeStatus

# 1. Base : Ce qui est commun à l'INPUT et à l'OUTPUT
# On garde seulement ce que le Front envoie et que l'API renvoie tel quel.
class RechargeBase(BaseModel):
    amount_eur: float = Field(gt=0, description="Montant en euros")
    payment_provider: str
    provider_reference: str

# 2. Create : Ce que le front envoie (INPUT)
# Ici, on n'a QUE les Euros. Pas d'USDC, pas de Jetons.
class RechargeCreate(RechargeBase):
    pass 

# 3. Read : Ce que l'API renvoie (OUTPUT)
# L'API enrichit la réponse avec les calculs du backend (USDC, Jetons, Status)
class RechargeRead(RechargeBase):
    id: UUID
    user_id: UUID
    status: RechargeStatus
    date: datetime
    
    # Ces champs sont calculés par le backend, ils apparaissent donc ici
    amount_usdc: float 
    units_granted: float

    class Config:
        from_attributes = True