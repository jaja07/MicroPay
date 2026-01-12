from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

# Ce que l'utilisateur envoie à l'inscription
class UserCreate(BaseModel):
    email: EmailStr
    password: str  # Mot de passe en clair à ce stade

# Ce que l'API renvoie (on cache le hashed_password)
class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True # Permet de convertir un objet SQLModel en ce Schema