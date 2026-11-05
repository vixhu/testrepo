from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, JSON, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class BlogContentSection(Base):
    __tablename__ = "blog_content_sections"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    blog_id = Column(BigInteger, nullable=False, index=True)

    section_order = Column(Integer, nullable=False, default=1)

    section_type = Column(
        Enum(
            "heading",
            "paragraph",
            "list",
            "image",
            "quote",
            "faq",
            "table",
            name="blog_section_type_enum"
        ),
        nullable=False
    )

    heading = Column(String(255), nullable=True)
    content = Column(JSON, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)