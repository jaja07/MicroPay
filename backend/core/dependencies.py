from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

from backend.repositories.user_repository import UserRepository
from backend.core.config import settings
from backend.models.user_entity import User
from backend.repositories.user_repository import UserRepository
from backend.db.session import SessionDep


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")
# Todo: Rendre la fonction asynchrone
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep # Utilise directement la session
) -> User:
    """Valide le token JWT dans l'entête de la requête et identifie l'utilisateur en vérifiant qu'il est 
    présent dans la base de données."""
    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # 2. On cherche l'user via un repository léger ou directement
    repository = UserRepository(session)
    user = repository.get_by_email(email)
    
    if user is None:
        raise credentials_exception
    return user
