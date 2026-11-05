from sqlalchemy import BigInteger, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.mysql import JSON

from app.database import Base
from app.utils.date_utils import get_utc_now


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    module = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    record_id = Column(BigInteger, nullable=True, index=True)
    record_name = Column(String(255), nullable=True)

    user_id = Column(BigInteger, nullable=True, index=True)
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)

    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    previous_values = Column(JSON, nullable=True)
    changed_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=get_utc_now, index=True)


Index("idx_activity_logs_module_record", ActivityLog.module, ActivityLog.record_id)
Index("idx_activity_logs_created_action", ActivityLog.created_at, ActivityLog.action)
