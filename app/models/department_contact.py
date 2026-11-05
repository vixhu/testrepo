from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class DepartmentContact(Base):
    __tablename__ = "department_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    department_name = Column(String(100), nullable=False)
    inquiry_type = Column(String(100))
    email = Column(String(255), nullable=False)

    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)