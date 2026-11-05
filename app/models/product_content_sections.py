from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, Enum, Integer, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class ProductContentSection(Base):
    __tablename__ = "product_content_sections"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    product_id = Column(BigInteger, nullable=False)

    section_order = Column(Integer, nullable=False, default=1)

    section_type = Column(
        Enum(
            "paragraph",
            "list",
            "feature_list",
            "table",
            "image",
            "faq",
            name="product_section_type",
        ),
        nullable=False,
    )

    heading = Column(String(255), nullable=True)

    content = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)