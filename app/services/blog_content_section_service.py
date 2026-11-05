from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.blog_content_section import BlogContentSection
from app.models.blog_media import BlogMedia
from app.schemas.blog_content_section import BlogContentSectionCreate, BlogContentSectionUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now
from app.utils.text import clean_product_text, clean_section_content


class BlogContentSectionService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def normalize_return(self, section=None, message: str | None = None, sections=None):
        def normalize_section(item: BlogContentSection):
            return {
                "id": item.id,
                "blog_id": item.blog_id,
                "section_order": item.section_order,
                "section_type": item.section_type,
                "heading": clean_product_text(item.heading),
                "content": clean_section_content(item.content),
                "is_active": bool(item.is_active),
                "created_at": format_datetime_ist(item.created_at) if item.created_at else None,
                "created_by": item.created_by,
                "updated_at": format_datetime_ist(item.updated_at) if item.updated_at else None,
                "updated_by": item.updated_by
            }

        payload = {}

        if message is not None:
            payload["message"] = message

        if sections is not None:
            payload["data"] = [normalize_section(item) for item in sections]
            return payload

        if section is not None:
            payload["data"] = normalize_section(section)
            return payload

        payload["data"] = None
        return payload

    def _link_media_to_blog(self, blog_id: int, media_id: int, user_id: int):
        existing_link = self.db.query(BlogMedia).filter(BlogMedia.blog_id == blog_id,BlogMedia.media_id == media_id).first()
        
        if not existing_link:
            blog_media = BlogMedia(
                blog_id=blog_id,
                media_id=media_id,
                is_featured=False,
                display_order=0,
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(blog_media)


    def create_blog_content_section(self, section_data: BlogContentSectionCreate, token):
        user = self.user_service.get_user_from_token(token)

        section = BlogContentSection(
            blog_id=section_data.blog_id,
            section_order=section_data.section_order,
            section_type=section_data.section_type,
            heading=clean_product_text(section_data.heading),
            content=clean_section_content(section_data.content),
            created_by=user.id,
            updated_by=user.id,
        )

        self.db.add(section)
        self.db.flush()

        if section_data.section_type == "image" and section_data.content:
            media_id = section_data.content.get("media_id")
            if media_id:
                self._link_media_to_blog(section_data.blog_id, media_id, user.id)

        self.db.commit()
        self.activity_log_service.record(module="Blog Content", action="Added", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Blog content section created", metadata={"blog_id": section.blog_id, "section_type": section.section_type}, commit=True)
        return self.normalize_return(section, "Blog content section created successfully")


    def get_blog_content_section_by_id(self, section_id: int, token):
        self.user_service.get_user_from_token(token)

        section = self.db.query(BlogContentSection).filter(BlogContentSection.id == section_id,BlogContentSection.is_active == True).first()
        if not section:
            return self.normalize_return(message="Blog content section not found")
        
        return self.normalize_return(section)


    def get_blog_content_sections_by_blog_id(self, blog_id: int, token):
        self.user_service.get_user_from_token(token)

        sections = self.db.query(BlogContentSection).filter(BlogContentSection.blog_id == blog_id, BlogContentSection.is_active == True).order_by(BlogContentSection.section_order.asc()).all()
        
        return self.normalize_return(sections=sections)


    def update_blog_content_section(self, section_id: int, section_data: BlogContentSectionUpdate, token):
        user = self.user_service.get_user_from_token(token)

        section = self.db.query(BlogContentSection).filter(BlogContentSection.id == section_id,BlogContentSection.is_active == True).first()

        if not section:
            return self.normalize_return(message="Blog content section not found")

        previous_values = self.activity_log_service.snapshot(section)
        if section_data.section_order is not None:
            section.section_order = section_data.section_order

        if section_data.section_type is not None:
            section.section_type = section_data.section_type

        if section_data.heading is not None:
            section.heading = clean_product_text(section_data.heading)

        if section_data.content is not None:
            section.content = clean_section_content(section_data.content)

        section.updated_by = user.id

        self.db.commit()

        if section.section_type == "image" and section.content:
            media_id = section.content.get("media_id")
            if media_id:
                self._link_media_to_blog(section.blog_id, media_id, user.id)
                self.db.commit()

        self.activity_log_service.record(module="Blog Content", action="Updated", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Blog content section updated", metadata={"blog_id": section.blog_id, "section_type": section.section_type}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, section), commit=True)
        return self.normalize_return(section, "Blog content section updated successfully")


    def delete_blog_content_section(self, section_id: int, token):
        user = self.user_service.get_user_from_token(token)

        section = self.db.query(BlogContentSection).filter(BlogContentSection.id == section_id,BlogContentSection.is_active == True).first()

        if not section:
            return self.normalize_return(message="Blog content section not found")

        previous_values = self.activity_log_service.snapshot(section, ["is_active"])
        section.is_active = False
        section.updated_by = user.id

        self.db.commit()
        self.activity_log_service.record(module="Blog Content", action="Deleted", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Blog content section deactivated", metadata={"blog_id": section.blog_id}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, section), commit=True)

        return self.normalize_return(message="Blog content section deleted successfully")


def get_blog_content_section_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> BlogContentSectionService:
    return BlogContentSectionService(db, user_service, activity_log_service)
