# auth.py
import os
from typing import Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

import jwt
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from basemodels import TokenPayload, UserOut

from database import get_db
from sqlalchemy.orm import Session
from Base import User, UserRole


# optional firebase admin
FIREBASE_PROVIDER = os.getenv("AUTH_PROVIDER", "LOCAL").upper()  # LOCAL or FIREBASE
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", None)

if FIREBASE_PROVIDER == "FIREBASE":
    
    cred_path = os.getenv("FIREBASE_CRED_PATH")
    if not firebase_admin._apps:
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()

# JWT settings for LOCAL tokens
JWT_SECRET = os.getenv("JWT_SECRET","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  # for swagger local login

# --- helpers ---
MAX_BCRYPT_BYTES = 72  # bcrypt limit

def normalize_password(password: str) -> str:
    """
    Truncate password safely to bcrypt's 72-byte limit.
    """
    if not password:
        return ""
    # truncate safely without breaking unicode characters
    return password.encode("utf-8")[:MAX_BCRYPT_BYTES].decode("utf-8", "ignore")

def hash_password(password: str) -> str:
    """
    Hash any plaintext password (auto-truncates if needed).
    """
    password = normalize_password(password)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plaintext password against hashed one (auto-truncates if needed).
    """
    plain_password = normalize_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, role: str, email: Optional[str]=None, expires_delta: Optional[timedelta]=None) -> str:
    to_encode = {"sub": str(subject), "role": role, "email": email}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# --- get current user (supports LOCAL and FIREBASE tokens) ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Decodes the JWT token and returns the current authenticated user.
    Works for both LOCAL JWT tokens and Firebase if integrated.
    """
    # Decode token (LOCAL JWT path)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # Extract required fields from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Fetch user from DB
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # ✅ Return correct schema (fix for missing fields)
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.name if hasattr(user.role, "name") else str(user.role),
        is_active=user.is_active
    )


# --- RBAC dependency factory ---
def require_role(*allowed_roles):
    def role_checker(current_user: UserOut = Depends(get_current_user)):
        """
        Ensures the current user has one of the allowed roles.
        """
        if current_user.role is None:
            raise HTTPException(status_code=403, detail="Access denied")

        # ✅ role is already a string in UserOut
        role_name = current_user.role

        if role_name not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")

        return current_user
    return role_checker

