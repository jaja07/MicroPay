from fastapi import APIRouter, Depends, HTTPException, status
from backend.schema.user import UserCreate, UserRead
from backend.services.user_service import UserService
from backend.repositories.user_repository import UserRepository
from backend.db.session import SessionDep

router = APIRouter(prefix="/users", tags=["Users"])

# --- Logique d'Injection de Dépendances ---

def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)

def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    # Plus tard, on injectera aussi le CircleService ici
    return UserService(repo)

# --- Endpoints ---

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    service: UserService = Depends(get_user_service)
):
    """
    Inscrit un nouvel utilisateur et déclenche la création du wallet.
    """
    # On vérifie si l'utilisateur existe déjà au niveau du service
    db_user = await service.register_user(email=user_data.email, password=user_data.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    return db_user