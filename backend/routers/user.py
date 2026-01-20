from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.schema.user import UserCreateDTO, UserReadDTO
from backend.schema.auth import VerifyOTPRequestUser
from backend.services.user_service import UserService
from backend.db.session import SessionDep

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]

@router.post("/", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateDTO,
    service: UserServiceDep,
):
    db_user = service.create_user(user_data)
    if not db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return db_user

@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequestUser, service: UserServiceDep):
    if service.verify_otp(request.email, request.otp_code):
        return {
            "status": 200,
            "message": "OTP vérifié avec succès"
                }
    raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")