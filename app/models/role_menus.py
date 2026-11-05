from sqlalchemy import BigInteger, Column, DateTime, Enum
from app.database import Base
from app.utils.date_utils import get_utc_now


class RoleMenu(Base):
    __tablename__ = "role_menus"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, nullable=False)
    admin_menu_id = Column(BigInteger, nullable=False)

    access_level = Column(
        Enum('None', 'Read', 'Write', name='role_menu_access_level_enum'),
        nullable=False,
        default='None'
    )

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
