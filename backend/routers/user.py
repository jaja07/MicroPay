

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.schema.user import UserCreateDTO, UserReadDTO, Token, TokenData
from backend.schema.auth import VerifyOTPRequestUser
from backend.services.user_service import UserService
from backend.services.auth_service import AuthService
from backend.db.session import SessionDep
from backend.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> Token:
    db_user = user_service.authenticate_user(form_data.username, form_data.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateDTO,
    user_service: UserServiceDep,
):
    db_user = user_service.create_user(user_data)
    if not db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return db_user

@router.post("/verify-otp")
async def verify_otp(
    request: VerifyOTPRequestUser,
    auth_service: AuthServiceDep
):
    if auth_service.verify_otp(request.email, request.otp_code):
        return {
            "status": 200,
            "message": "OTP vérifié avec succès"
                }
    raise HTTPException(status_code=400, detail="Code OTP invalide ou expiré")