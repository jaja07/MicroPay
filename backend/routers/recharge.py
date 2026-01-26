# backend/routers/recharges.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID

from backend.db.session import get_session
from backend.services.recharge_service import RechargeService
from backend.schema.recharges import RechargeInitRequest, RechargeInitResponse

router = APIRouter(prefix="/recharges", tags=["Recharges"])

# ---------------------------------------------------------
# TODO : récupérer le user_id dans la session 
# de l'utilisateur connecté en utilisant son token JWT
# ---------------------------------------------------------

@router.post("/init-payment", response_model=RechargeInitResponse)
def init_payment(
    req: RechargeInitRequest, 
    session: Session = Depends(get_session)
):
    """
    Initie un paiement en partant d'un nombre d'UNITÉS.
    Exemple Input: { "units": 50 }
    """
    fake_user_id = UUID("add3f367-bfce-493d-bbb6-a1885452fa21")

    print(f"TEST MODE: Demande de {req.units} unités pour user {fake_user_id}")
    
    service = RechargeService(session)
    return service.init_payment_by_units(fake_user_id, req.units)