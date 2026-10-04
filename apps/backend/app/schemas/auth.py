from pydantic import BaseModel
from typing import Optional
from app.schemas.enums import UserRole

class PlatformLoginRequest(BaseModel):
    username: str
    password: str

class PlatformTokenResponse(BaseModel):
    access_token: str
    token_type: str
    
class UserProfile(BaseModel):
    user_id: str
    username: str
    name: str
    role: UserRole
    outlet_id: Optional[str] = None
    depot_id: Optional[str] = None

    model_config = {"from_attributes": True}
