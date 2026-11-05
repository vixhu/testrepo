from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, func
from app.database import Base
from app.utils.date_utils import get_utc_now


class Catalogue(Base):
    __tablename__ = "catalogues"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    pdf_url = Column(String(500), nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now, index=True)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)