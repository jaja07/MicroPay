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

# ---------------------------------------------------------
# TODO : récupérer le user_id dans la session 
# de l'utilisateur connecté en utilisant son token JWT
# ---------------------------------------------------------

@router.post("/init-payment", response_model=RechargeInitResponse)
def init_payment(
    req: RechargeInitRequest, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Initie un paiement en partant d'un nombre d'UNITÉS.
    Exemple Input: { "units": 50 }
    """
    user_id = current_user.id

    print(f"TEST MODE: Demande de {req.units} unités pour user {user_id}")
    
    service = RechargeService(session)
    return service.init_payment_by_units(user_id, req.units)