from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, String

from app.database import Base
from app.utils.date_utils import get_utc_now


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, nullable=True, index=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    author_name = Column(String(255), nullable=True)
    author_image_url = Column(String(500), nullable=True)

    status = Column(Enum("draft", "published", "scheduled", name="blog_status_enum"), nullable=False, default="draft", index=True)

    published_at = Column(DateTime, nullable=True)
    scheduled_publish_at = Column(DateTime, nullable=True, index=True)

    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    view_count = Column(BigInteger, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)