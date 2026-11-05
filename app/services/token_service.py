from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError, decode as jwt_decode, encode as jwt_encode
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.password_reset_tokens import PasswordResetToken
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now

oauth2_scheme = HTTPBearer(auto_error=True)

def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    return credentials.credentials

class TokenService:
    def __init__(self, db):
        self.db = db


    @staticmethod
    def verify_access_token(token: str):
        try:
            payload = jwt_decode(token, settings.access_secret, algorithms=[settings.algorithm])
            return payload["sub"]
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail = "Token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail = "Invalid Token")
        
    @staticmethod
    def verify_temp_token(token: str):
        try:
            payload = jwt_decode(token, settings.temp_secret, algorithms=[settings.algorithm])
            return payload["sub"]
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail = "Token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail = "Invalid Token")

    def invalidate_unused_reset_tokens(self, user_id: int):
        reset_tokens = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at <= get_utc_now()).all()

        for token in reset_tokens:
            token.is_used = True
            token.updated_at = get_utc_now()

        self.db.commit()

    @staticmethod
    def decode_token(token: str, secret: str):
        try:
            payload = jwt_decode(token, secret, algorithms=[settings.algorithm])
            return payload["sub"]
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid or expired Token")

    def create_reset_token(self, user_id: int, user_role: str):
        return self.create_jwt_token(
            data={"sub": str(user_id),"role": user_role},
            secret=settings.temp_secret,
            expires_delta=timedelta(minutes=settings.reset_token_expire_minutes),
        )
    
    def create_refresh_token(self, user_id: int, user_role: str):
        token_data = {
            "sub": str(user_id),
            "role": user_role
        }
        return self.create_jwt_token(token_data, settings.refresh_secret, timedelta(days=settings.refresh_token_expire_days))

    def create_access_token(self, user_id: int, user_role: str):
        return self.create_jwt_token(
            data={"sub": str(user_id), "role": user_role},
            secret=settings.access_secret,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
    
    @staticmethod
    def create_jwt_token(data: dict, secret: str, expires_delta: timedelta):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        return jwt_encode(to_encode, secret, algorithm=settings.algorithm)

    def create_temp_token(self, user_id: int, user_role: str):
        return self.create_jwt_token(
            data={"sub": str(user_id), "role": user_role},
            secret=settings.temp_secret,
            expires_delta=timedelta(minutes=settings.reset_token_expire_minutes))


def get_token_service(
        db: Session = Depends(get_db)) -> TokenService:
    return TokenService(db)


