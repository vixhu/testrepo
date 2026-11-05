from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text
from app.database import Base
from app.utils.date_utils import get_utc_now


class BlogCategory(Base):
    __tablename__ = "blog_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=False)

    slug = Column(String(255), unique=True, nullable=False)

    description = Column(Text)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=get_utc_now)

    created_by = Column(Integer)

    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    updated_by = Column(Integer)