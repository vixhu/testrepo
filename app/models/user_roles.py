from sqlalchemy import BigInteger, Column, DateTime
from app.database import Base
from app.utils.date_utils import get_utc_now


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(BigInteger, nullable=False)
    role_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=False)

    updated_at = Column(DateTime, nullable=True, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)