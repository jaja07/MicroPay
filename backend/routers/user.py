from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from schema.user import UserCreateDTO, UserReadDTO
from services.user_service import UserService
from db.session import SessionDep

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