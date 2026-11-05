from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from app.database import Base
from app.utils.date_utils import get_utc_now


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    page_id = Column(BigInteger, nullable=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    short_description = Column(Text, nullable=True)

    category_id = Column(BigInteger, nullable=False)

    featured_image_id = Column(BigInteger, nullable=True)
    datasheet_file_id = Column(BigInteger, nullable=True)
    video_file_id = Column(BigInteger, nullable=True)

    youtube_url = Column(String(500), nullable=True)
    specifications = Column(JSON, nullable=True)
    industry_tag_id = Column(JSON, nullable=True)

    status = Column(Enum("upcoming", "launched", name="product_status_enum"), nullable=False, default="upcoming")
    display_order = Column(Integer, nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)


