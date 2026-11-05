from sqlalchemy import BigInteger, Column, DateTime, String, Text
from app.database import Base
from app.utils.date_utils import get_utc_now


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    is_admin_access_enabled = Column(BigInteger, nullable=False, default=0)
    is_enabled = Column(BigInteger, nullable=False, default=1)

    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, nullable=False, default=get_utc_now)

    updated_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=get_utc_now)
