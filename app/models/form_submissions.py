from sqlalchemy import BigInteger, Column, DateTime, Enum, String, Text, Boolean
from app.database import Base
from app.utils.date_utils import get_utc_now

class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    form_id = Column(BigInteger, nullable=True, index=True)

    form_type = Column(Enum('contact', 'datasheet', 'career', 'catalogue', 'general', name='form_type_enum'),nullable=False,default='contact',index=True)

    product_id = Column(BigInteger, nullable=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    message = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    attachment_url = Column(Text, nullable=True)

    ip_address = Column(String(45), nullable=True)      
    user_agent = Column(Text, nullable=True)           
    device_type = Column(String(50), nullable=True)     
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    auto_reply_sent = Column(Boolean, default=False, nullable=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now, index=True)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
    updated_by = Column(BigInteger, nullable=True)
