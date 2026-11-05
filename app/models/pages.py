from sqlalchemy import BigInteger, Column, DateTime, Enum, String
from app.database import Base
from app.utils.date_utils import get_utc_now


class Page(Base):
    __tablename__ = "pages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    page_type = Column(
        Enum(
            "home",
            "product",
            "market",
            "about",
            "contact",
            "blog",
            "generic",
            name="page_type_enum"
        ),
        nullable=False,
        default="generic",
        index=True
    )

    status = Column(Enum("draft","published", name="page_status_enum"),nullable=False,default="published")

    created_at = Column(DateTime,nullable=False,default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime,nullable=False,default=get_utc_now,onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)