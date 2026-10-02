from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_password, create_platform_access_token
from app.schemas.auth import PlatformLoginRequest, PlatformTokenResponse, UserProfile
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=PlatformTokenResponse)
def login(request: PlatformLoginRequest, db: Session = Depends(get_db)):
    """Authenticate User and return JWT token."""
    user = db.query(User).filter(User.username == request.username).first()
    
    # Verify user exists and password is correct using bcrypt
    if not user or not verify_password(request.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
        
    # Include role and scope data directly in JWT to avoid DB lookups if preferred,
    # but sub is enough since get_current_user loads the whole user.
    token_payload = {
        "sub": user.user_id,
        "role": user.role,
        "outlet_id": user.outlet_id,
        "depot_id": user.depot_id
    }
    
    access_token = create_platform_access_token(token_payload)
    return PlatformTokenResponse(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user profile."""
    return current_user
