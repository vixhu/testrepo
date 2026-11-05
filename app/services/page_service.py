from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pages import Page
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


class PageService:
    def __init__(
        self,
        db,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def _serialize_page(self, page):
        return {
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "page_type": page.page_type,
            "status": page.status,
            "created_at": page.created_at,
            "created_by": page.created_by,
            "updated_at": page.updated_at,
            "updated_by": page.updated_by,
        }

    def _ensure_slug_available(self, slug: str, exclude_page_id: int = None):
        from app.utils.query import ensure_slug_available
        ensure_slug_available(
            self.db, Page, slug, exclude_id=exclude_page_id, detail="Page with this slug already exists"
        )

    def get_pages(self, token: str):
        self.user_service.get_user_from_token(token)
        pages = self.db.query(Page).order_by(Page.page_type.asc(), Page.title.asc()).all()
        return [self._serialize_page(page) for page in pages]

    def get_page_by_slug(self, slug: str, token: str):
        self.user_service.get_user_from_token(token)
        page = self.db.query(Page).filter(Page.slug == slug).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return self._serialize_page(page)

    def get_page_content(self, slug: str, token: str):
        self.user_service.get_user_from_token(token)
        page = self.db.query(Page).filter(Page.slug == slug).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")

        return {
            "page": self._serialize_page(page),
            "sections": [],
        }

    def create_page(self, page_data, token: str):
        user = self.user_service.get_user_from_token(token)
        self._ensure_slug_available(page_data.slug)
        page = Page(
            title=page_data.title,
            slug=page_data.slug,
            page_type=page_data.page_type,
            status=page_data.status,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        self.activity_log_service.record(
            module="Pages",
            action="Added",
            record_id=page.id,
            record_name=page.title,
            user=user,
            description="Page created",
            metadata={"status": page.status, "page_type": page.page_type},
            commit=True,
        )
        return {"message": "Page created successfully", "id": page.id}

    def update_page(self, page_id: int, page_data, token: str):
        user = self.user_service.get_user_from_token(token)
        page = self.db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")

        previous_values = self.activity_log_service.snapshot(page)
        update_data = page_data.model_dump(exclude_unset=True)
        if "slug" in update_data:
            self._ensure_slug_available(update_data["slug"], exclude_page_id=page.id)
        for field_name, value in update_data.items():
            setattr(page, field_name, value)

        page.updated_by = user.id
        self.db.commit()
        self.db.refresh(page)
        self.activity_log_service.record(
            module="Pages",
            action="Updated",
            record_id=page.id,
            record_name=page.title,
            user=user,
            description="Page updated",
            metadata={"fields": list(update_data.keys())},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, page),
            commit=True,
        )
        return {"message": "Page updated successfully", "id": page.id}


def get_page_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> PageService:
    return PageService(db, user_service, activity_log_service)
