from pydantic import BaseModel, EmailStr
from uuid import UUID

class WalletDTO(BaseModel):
    user_id: UUID
    circle_wallet_id: str
    address: str
    blockchain: str
    account_type: str
    state: str
    wallet_set_id: str

class WalletReadDTO(WalletDTO):
    id: UUID

    class Config:
        from_attributes = True