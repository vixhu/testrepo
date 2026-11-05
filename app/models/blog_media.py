from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, func
from app.database import Base
from app.utils.date_utils import get_utc_now


class BlogMedia(Base):
    __tablename__ = "blog_media"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    blog_id = Column(BigInteger,  nullable=False)
    media_id = Column(BigInteger, nullable=False)
    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)

  