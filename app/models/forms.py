from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, String, Text
from app.database import Base
from app.utils.date_utils import get_utc_now


class Form(Base):
    __tablename__ = "forms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    form_type = Column(
        Enum("contact", "datasheet", "career", "catalogue", "general", name="forms_form_type_enum"),
        nullable=False,
    )
    recipient_email = Column(String(255), nullable=False)
    auto_reply_subject = Column(String(255), nullable=True)
    auto_reply_message = Column(Text, nullable=True)
    auto_reply_enabled = Column(Boolean, nullable=False, default=True)
    cc_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=get_utc_now)
    updated_at = Column(DateTime, nullable=False, default=get_utc_now, onupdate=get_utc_now)
