from fastapi import APIRouter, Depends
from core.dependencies import get_current_user

router = APIRouter(prefix="/wallet", tags=["wallet"])

CurrentUserDep = Depends(get_current_user)

