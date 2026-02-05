# backend/routers/recharges.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID
from backend.models.user_entity import User
from backend.db.session import get_session
from backend.services.recharge_service import RechargeService
from backend.schema.recharges import RechargeInitRequest, RechargeInitResponse
from backend.core.dependencies import get_current_user

router = APIRouter(prefix="/recharges", tags=["Recharges"])


@router.post("/init-payment", response_model=RechargeInitResponse)
def init_payment(
    req: RechargeInitRequest, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # 🔒 Protection de la route
):
    """
    Initie un paiement Stripe pour acheter des crédits.
    L'utilisateur doit être connecté (Header Authorization: Bearer <token>).
    """
    
    # Petit log pour le debug
    #print(f" Init Payment par : {current_user.email} (ID: {current_user.id})")
    #print(f" Unités demandées : {req.units}")

    # On instancie le service
    service = RechargeService(session)
    
    # On lance la logique métier avec le VRAI ID de l'utilisateur connecté
    return service.init_payment_by_units(user_id=current_user.id, units=req.units)