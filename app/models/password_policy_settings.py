from sqlalchemy import Column, Integer, Boolean, SmallInteger, DateTime
from app.database import Base
from app.utils.date_utils import get_utc_now

class PasswordPolicySetting(Base):
    __tablename__ = "password_policy_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    min_length = Column(Integer, nullable=False, default=8)
    max_length = Column(Integer, nullable=False, default=128)

    require_uppercase = Column(Boolean, nullable=False, default=True)
    require_lowercase = Column(Boolean, nullable=False, default=True)
    require_number = Column(Boolean, nullable=False, default=True)
    require_special_char = Column(Boolean, nullable=False, default=True)

    allow_previous_passwords = Column(Integer, nullable=False, default=5)

    max_attempts = Column(SmallInteger, nullable=False, default=5)
    lockout_duration_minutes = Column(SmallInteger, nullable=False, default=15)
    password_expiry_days = Column(SmallInteger, nullable=False, default=90)

    created_at = Column(DateTime, nullable=True, default=get_utc_now)