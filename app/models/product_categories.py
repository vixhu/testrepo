from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Integer
from app.database import Base
from app.utils.date_utils import get_utc_now


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)

    parent_id = Column(BigInteger, nullable=True)      # Parent category mapping
    display_order = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
