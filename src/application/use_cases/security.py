# security.py
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from infrastructure.database import get_db
from domain.models.user_models import TokenPayload
from domain.entities.user_entity import User as UserORM
from domain.entities.user_classes import UserEntity, RoleType

pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

JWT_SECRET = os.environ.get("JWT_SECRET", "change_this_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def hash_password(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("Password must be a string")
    return pwd_context.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    if not isinstance(raw, str):
        return False
    return pwd_context.verify(raw, hashed)

def create_access_token(*, email: str, role: RoleType, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "role": role.value, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def parse_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return TokenPayload(sub=payload.get("sub"), role=payload.get("role"))
    except (JWTError, ValidationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserEntity:
    payload = parse_token(token)
    user: UserORM | None = db.query(UserORM).filter(UserORM.email == payload.sub).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    return UserEntity(id=user.id, email=user.email, full_name=user.full_name, role=RoleType(role_value), is_active=user.is_active)

def require_roles(*allowed: RoleType):
    def _checker(current: UserEntity = Depends(get_current_user)) -> UserEntity:
        if current.role not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current
    return _checker
