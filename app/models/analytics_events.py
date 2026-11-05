from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, String, Text, func
from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_type = Column(Enum("form_submission", "newsletter_signup", "contact_button_click", "email_click", "whatsapp_click", "catalogue_download", "datasheet_download", "annual_return_download", "product_click", "product_category_click", name="analytics_event_type_enum"), nullable=False)
    reference_id = Column(BigInteger, nullable=True)
    reference_type = Column(Enum("product", "product_category", "blog", "page", "form", name="analytics_reference_type_enum"), nullable=True)
    page_slug = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    