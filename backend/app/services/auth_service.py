from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog

from app.models.user import User
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.config import settings

logger = structlog.get_logger()


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning("Authentication failed: user not found", email=email)
            return None
        
        if not user.verify_password(password):
            logger.warning("Authentication failed: invalid password", email=email)
            return None
        
        if not user.is_active:
            logger.warning("Authentication failed: inactive user", email=email)
            return None
        
        logger.info("User authenticated successfully", user_id=user.id, email=email)
        return user

    async def create_user(self, email: str, full_name: str, password: str) -> User:
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        user = User(
            email=email,
            full_name=full_name,
            password=password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info("User created successfully", user_id=user.id, email=email)
        return user

    async def generate_tokens(self, user: User) -> Dict[str, Any]:
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, 
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        from app.core.security import verify_token
        
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token")
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=7)
        
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        refresh_token = create_access_token(
            data={"sub": str(user.id), "type": "refresh"}, 
            expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            import uuid
            user_uuid = uuid.UUID(user_id)
            return self.db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            return None

    async def update_user_last_login(self, user: User):
        user.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info("User last login updated", user_id=user.id)

    async def deactivate_user(self, user: User):
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info("User deactivated", user_id=user.id)

    async def activate_user(self, user: User):
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info("User activated", user_id=user.id)
