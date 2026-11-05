from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.database import Base
from app.utils.date_utils import get_utc_now

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, nullable=False)

    reset_token = Column(String(255), nullable=False, index=True)

    expires_at = Column(DateTime, nullable=False)

    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(Integer, nullable=False)
