

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from uuid import UUID

from backend.schema.user import UserCreateDTO, UserReadDTO, Token, UserUpdateDTO
from backend.schema.auth import VerifyOTPRequestUser
from backend.services.user_service import UserService
from backend.services.auth_service import AuthService
from backend.models.user_entity import User
from backend.db.session import SessionDep
from backend.core.config import settings
from backend.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]

@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> Token:
    """Authenticate a user and generate a JWT token for the upcoming resuests."""

    db_user = user_service.authenticate_user(form_data.username, form_data.password)

    if db_user is None:
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

@router.get("/me", response_model=UserReadDTO)
def read_user_me(
    current_user: CurrentUserDep
):
    """Get the current authenticated user's information."""
    return current_user

@router.get("/{user_id}", response_model=UserReadDTO)
def read_user(
    user_id: UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
):
    """Get a user by ID. Only the user themselves or an admin can access this endpoint."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
    
    db_user = user_service.get_user(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.put("/{user_id}", response_model=UserReadDTO)
def update_user(
    user_id: UUID,
    user_data: UserUpdateDTO,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    updated_user = user_service.update_user(user_id, user_data=user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")