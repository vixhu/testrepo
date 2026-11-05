from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text
from app.database import Base
from app.utils.date_utils import get_utc_now


class AnnualReturn(Base):
    __tablename__ = "annual_returns"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    title = Column(String(255), nullable=True)
    pdf_file_url = Column(String(2000), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
