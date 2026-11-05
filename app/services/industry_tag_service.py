from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product_industry_tags import IndustryTag
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist
from app.utils.query import get_or_404


class IndustryTagService:
    def __init__(self, db: Session, user_service: UserService):
        self.db = db
        self.user_service = user_service

    def _serialize_date(self, value):
        return format_datetime_ist(value) if value else None

    def _serialize(self, tag: IndustryTag):
        return {
            "id": tag.id,
            "name": tag.name,
            "is_active": bool(tag.is_active),
            "created_at": self._serialize_date(tag.created_at),
            "created_by": tag.created_by,
            "updated_at": self._serialize_date(tag.updated_at),
            "updated_by": tag.updated_by,
        }

    def get_all_tags(self, token: str, is_active: bool = None):
        self.user_service.get_user_from_token(token)

        query = self.db.query(IndustryTag)

        if is_active is not None:
            query = query.filter(IndustryTag.is_active == is_active)

        tags = query.order_by(IndustryTag.is_active.desc(), IndustryTag.name.asc()).all()

        return [self._serialize(tag) for tag in tags]

    def get_tag_by_id(self, tag_id: int, token: str):
        self.user_service.get_user_from_token(token)

        tag = get_or_404(self.db, IndustryTag, tag_id, "Industry tag not found")

        return self._serialize(tag)


def get_industry_tag_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> IndustryTagService:
    return IndustryTagService(db, user_service)
