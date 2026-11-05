from app.utils.date_utils import format_datetime_ist
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import re

from fastapi import Depends
from sqlalchemy import or_
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.activity_logs import ActivityLog
from app.models.users import User


class ActivityLogService:
    DATE_FORMAT = "%d/%b/%Y"
    DATE_TIME_FORMAT = "%d/%b/%Y %I:%M %p"

    SENSITIVE_FIELDS = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "reset_token",
    }

    def __init__(self, db: Session):
        self.db = db

    def table_exists(self) -> bool:
        try:
            return inspect(self.db.bind).has_table(ActivityLog.__tablename__)
        except Exception:
            return False

    def record(
        self,
        module: str,
        action: str,
        record_id: int | None = None,
        record_name: str | None = None,
        user: User | None = None,
        description: str | None = None,
        metadata: dict | None = None,
        previous_values: dict | None = None,
        changed_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        commit: bool = False,
    ) -> ActivityLog | None:
        if not self.table_exists():
            return None

        try:
            activity = ActivityLog(
                module=module,
                action=action,
                record_id=record_id,
                record_name=record_name,
                user_id=user.id if user else None,
                user_name=user.full_name if user else None,
                user_email=user.email if user else None,
                description=description,
                metadata_json=metadata,
                previous_values=self._json_safe(previous_values),
                changed_values=self._json_safe(changed_values),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(activity)

            if commit:
                self.db.commit()
                self.db.refresh(activity)

            return activity
        except Exception:
            self.db.rollback()
            return None

    def snapshot(self, entity, fields: list[str] | None = None) -> dict:
        columns = fields or [column.key for column in inspect(entity).mapper.column_attrs]
        return {
            field: self._json_safe(getattr(entity, field))
            for field in columns
            if field not in self.SENSITIVE_FIELDS and hasattr(entity, field)
        }

    def changes(self, previous_values: dict, entity) -> dict:
        current_values = self.snapshot(entity, list(previous_values.keys()))
        return {
            field: {"from": previous_values.get(field), "to": current_value}
            for field, current_value in current_values.items()
            if previous_values.get(field) != current_value
        }

    def _json_safe(self, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat() + ("Z" if value.tzinfo is None else "")
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        return str(value)

    def format_datetime(self, value) -> str | None:
        return format_datetime_ist(value, self.DATE_TIME_FORMAT)

    def format_stored_values(self, value):
        if isinstance(value, dict):
            return {key: self.format_stored_values(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.format_stored_values(item) for item in value]
        if isinstance(value, str):
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d")
                    return format_datetime_ist(dt, self.DATE_FORMAT)
                except ValueError:
                    return value
            if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
                try:
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    return format_datetime_ist(dt, self.DATE_TIME_FORMAT)
                except ValueError:
                    return value
        return value

    def list_recent(self, limit: int = 30):
        if not self.table_exists():
            return []

        try:
            return (
                self.db.query(ActivityLog)
                .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
                .limit(limit)
                .all()
            )
        except Exception:
            self.db.rollback()
            return []

    def search(
        self,
        page: int = 1,
        limit: int = 50,
        module: str | None = None,
        action: str | None = None,
        user_id: int | None = None,
        search: str | None = None,
    ):
        if not self.table_exists():
            return {"data": [], "page": page, "limit": limit, "total": 0, "total_pages": 0}

        query = self.db.query(ActivityLog)
        if module:
            query = query.filter(ActivityLog.module == module)
        if action:
            query = query.filter(ActivityLog.action == action)
        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ActivityLog.record_name.ilike(pattern),
                    ActivityLog.user_name.ilike(pattern),
                    ActivityLog.user_email.ilike(pattern),
                    ActivityLog.description.ilike(pattern),
                )
            )

        total = query.count()
        rows = (
            query.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return {
            "data": [
                {
                    "id": row.id,
                    "module": row.module,
                    "action": row.action,
                    "record_id": row.record_id,
                    "record_name": row.record_name,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "description": row.description,
                    "metadata": self.format_stored_values(row.metadata_json),
                    "previous_values": self.format_stored_values(row.previous_values),
                    "changed_values": self.format_stored_values(row.changed_values),
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "created_at": self.format_datetime(row.created_at),
                }
                for row in rows
            ],
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        }


def get_activity_log_service(db: Session = Depends(get_db)) -> ActivityLogService:
    return ActivityLogService(db)
