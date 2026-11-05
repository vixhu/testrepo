from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    menu_id = Column(BigInteger, nullable=False)
    parent_id = Column(BigInteger, nullable=True)

    title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
