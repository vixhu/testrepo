from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, JSON, String, Text, UniqueConstraint
from app.database import Base
from app.utils.date_utils import get_utc_now


class SEO(Base):
    __tablename__ = "seo"

    __table_args__ = (UniqueConstraint("reference_type", "reference_id", name="uq_seo_reference"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reference_type = Column(Enum("page", "product", "post", "career", "product_category", name="seo_reference_type_enum"), nullable=False, index=True)
    reference_id = Column(BigInteger, nullable=False, index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    canonical_url = Column(String(500), nullable=True)
    og_title = Column(String(255), nullable=True)
    og_description = Column(Text, nullable=True)
    og_image_id = Column(BigInteger, nullable=True)
    target_keywords = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)