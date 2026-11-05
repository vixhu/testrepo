from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class AdminMenu(Base):
    __tablename__ = "admin_menus"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    icon = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
