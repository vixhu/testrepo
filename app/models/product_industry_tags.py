from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, func
from app.database import Base
from app.utils.date_utils import get_utc_now

class IndustryTag(Base):
    __tablename__ = "product_industry_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_utc_now)
    created_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(Integer, nullable=True)