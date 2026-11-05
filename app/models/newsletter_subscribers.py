from sqlalchemy import BigInteger, Column, DateTime, String, Boolean
from app.database import Base
from app.utils.date_utils import get_utc_now

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=get_utc_now)