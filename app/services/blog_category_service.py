from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.blog_categories import BlogCategory
from app.models.blog_posts import BlogPost
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


class BlogCategoryService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    # Replaced _require_admin with self.user_service._require_permission

    def _serialize_category(self, category):
        return {
            "id": category.id,
            "category_id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "is_active": bool(category.is_active),
            "created_at": category.created_at,
            "created_by": category.created_by,
            "updated_at": category.updated_at,
            "updated_by": category.updated_by,
        }

    def _ensure_slug_available(self, slug: str, exclude_category_id: int = None):
        from app.utils.query import ensure_slug_available
        ensure_slug_available(
            self.db,
            BlogCategory,
            slug,
            exclude_id=exclude_category_id,
            detail="Blog category with this slug already exists",
        )

    def get_all_categories(self, token: str):
        self.user_service.get_user_from_token(token)
        categories = self.db.query(BlogCategory).order_by(BlogCategory.is_active.desc(), BlogCategory.name.asc()).all()

        return [self._serialize_category(category) for category in categories]

    def get_category_by_id(self, category_id: int, token: str):
        self.user_service.get_user_from_token(token)
        
        category = self.db.query(BlogCategory).filter(BlogCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return self._serialize_category(category)

    def create_category(self, payload, token: str):
        user = self.user_service.get_user_from_token(token)
        self._ensure_slug_available(payload.slug)
        category = BlogCategory(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            is_active=payload.is_active,
            created_by=user.id,
            updated_by=user.id)

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        self.activity_log_service.record(
            module="Blog Categories",
            action="Added",
            record_id=category.id,
            record_name=category.name,
            user=user,
            description="Blog category created",
            commit=True,
        )

        return {
            "message": "Category created successfully",
            "category": self._serialize_category(category)
        }

    def update_category(self, category_id: int, blog_category_update, token: str):
        user = self.user_service.get_user_from_token(token)

        category = self.db.query(BlogCategory).filter(BlogCategory.id == category_id).first()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        previous_values = self.activity_log_service.snapshot(category)
        if blog_category_update.slug is not None:
            self._ensure_slug_available(blog_category_update.slug, exclude_category_id=category.id)

        if blog_category_update.name is not None:
            category.name = blog_category_update.name
        if blog_category_update.slug is not None:
            category.slug = blog_category_update.slug
        if blog_category_update.description is not None:
            category.description = blog_category_update.description
        if blog_category_update.is_active is not None:
            category.is_active = blog_category_update.is_active

        category.updated_by = user.id

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        self.activity_log_service.record(
            module="Blog Categories",
            action="Updated",
            record_id=category.id,
            record_name=category.name,
            user=user,
            description="Blog category updated",
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, category),
            commit=True,
        )

        return {
            "message": "Category updated successfully",
            "category": self._serialize_category(category),
        }

    def toggle_category_status(self, category_id: int, token: str):
        user = self.user_service.get_user_from_token(token)

        category = (
            self.db.query(BlogCategory)
            .filter(BlogCategory.id == category_id)
            .first()
        )

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        previous_values = self.activity_log_service.snapshot(category, ["is_active"])
        category.is_active = not category.is_active

        self.db.commit()
        self.db.refresh(category)
        self.activity_log_service.record(
            module="Blog Categories",
            action="Activated" if category.is_active else "Deactivated",
            record_id=category.id,
            record_name=category.name,
            user=user,
            description="Blog category status changed",
            metadata={"is_active": category.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, category),
            commit=True,
        )

        return {
            "message": f"Category {'activated' if category.is_active else 'deactivated'} successfully",
            "category": self._serialize_category(category),
        }


def get_blog_category_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> BlogCategoryService:
    return BlogCategoryService(db, user_service, activity_log_service)
