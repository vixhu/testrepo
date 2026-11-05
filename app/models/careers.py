from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Enum, JSON, String

from app.database import Base
from app.utils.date_utils import get_utc_now


class Career(Base):
    __tablename__ = "careers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    department = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=True)

    employment_type = Column(
        Enum("full-time", "part-time", "contract", "internship", name="employment_type_enum"),
        nullable=False,
        default="full-time",
        index=True,
    )

    description = Column(JSON, nullable=False)

    experience_min_years = Column(String(20), nullable=True)

    salary_min = Column(BigInteger, nullable=True)
    salary_max = Column(BigInteger, nullable=True)
    salary_currency = Column(String(10), nullable=True)

    status = Column(
        Enum("open", "closed", "on-hold", name="career_status_enum"),
        nullable=False,
        default="open",
        index=True,
    )

    featured = Column(Boolean, nullable=False, default=False, index=True)
    form_id = Column(BigInteger, nullable=True)

    posted_at = Column(DateTime, nullable=True)
    closing_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    created_by = Column(BigInteger, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)