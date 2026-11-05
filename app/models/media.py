from sqlalchemy import BigInteger, Column, DateTime, String, Text
from app.database import Base
from app.utils.date_utils import get_utc_now


class Media(Base):
    __tablename__ = "media"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    file_name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)

    mime_type = Column(String(100), nullable=True)

    alt_text = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)