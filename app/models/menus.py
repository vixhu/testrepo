from sqlalchemy import BigInteger, Column, DateTime, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class Menu(Base):
    __tablename__ = "menus"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
