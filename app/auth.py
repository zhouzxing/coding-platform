"""Password hashing (SHA-256+salt) + JWT + FastAPI user dependency."""
from __future__ import annotations
import hashlib, os, secrets
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from db import User, get_session

JWT_SECRET = os.environ.get("CODING_JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7

_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None):
    if salt is None:
        salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return h, salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    h, _ = hash_password(password, salt)
    return secrets.compare_digest(h, expected_hash)

def create_token(user: User) -> str:
    import datetime as _dt
    payload = {"sub": str(user.id), "username": user.username,
               "exp": _dt.datetime.now(_dt.timezone.utc).timestamp() + JWT_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    data = decode_token(creds.credentials)
    user_id = int(data.get("sub", 0))
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
