from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product_content_sections import ProductContentSection
from app.schemas.product_content_section import ProductContentSectionCreate, ProductContentSectionUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now
from app.utils.text import clean_product_text, clean_section_content


class ProductContentSectionService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):

        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def normalize_return(self, section=None, message: str | None = None, sections=None):
        def normalize_section(item: ProductContentSection):
            return {
                "id": item.id,
                "product_id": item.product_id,
                "section_order": item.section_order,
                "section_type": item.section_type,
                "heading": item.heading,
                "content": item.content,
                "is_active": bool(item.is_active),
                "created_at": format_datetime_ist(item.created_at) if item.created_at else None,
                "created_by": item.created_by,
                "updated_at": format_datetime_ist(item.updated_at) if item.updated_at else None,
                "updated_by": item.updated_by,
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

    def create_product_content_section(self, section_data: ProductContentSectionCreate, token):
        user = self.user_service.get_user_from_token(token)

        section = ProductContentSection(
            product_id=section_data.product_id,
            section_order=section_data.section_order,
            section_type=section_data.section_type,
            heading=clean_product_text(section_data.heading),
            content=clean_section_content(section_data.content),
            created_by=user.id,
            updated_by=user.id,
        )

        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)
        self.activity_log_service.record(module="Product Content", action="Added", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Product content section created", metadata={"product_id": section.product_id, "section_type": section.section_type}, commit=True)

        return self.normalize_return(section, "Product content section created successfully")

    def get_product_content_section_by_id(self, section_id: int, token):
        self.user_service.get_user_from_token(token)

        section = self.db.query(ProductContentSection).filter(
            ProductContentSection.id == section_id,
            ProductContentSection.is_active == True
        ).first()
        if not section:
            return self.normalize_return(message="Product content section not found")

        return self.normalize_return(section)

    def get_product_content_sections_by_product_id(self, product_id: int, token):
        self.user_service.get_user_from_token(token)

        sections = self.db.query(ProductContentSection).filter(
            ProductContentSection.product_id == product_id,
            ProductContentSection.is_active == True
        ).order_by(ProductContentSection.section_order.asc()).all()

        return self.normalize_return(sections=sections)

    def update_product_content_section(self, section_id: int, section_data: ProductContentSectionUpdate, token):
        user = self.user_service.get_user_from_token(token)

        section = self.db.query(ProductContentSection).filter(
            ProductContentSection.id == section_id,
            ProductContentSection.is_active == True
        ).first()

        if not section:
            return self.normalize_return(message="Product content section not found")

        previous_values = self.activity_log_service.snapshot(section)
        if section_data.product_id is not None:
            section.product_id = section_data.product_id

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
        self.db.refresh(section)
        self.activity_log_service.record(module="Product Content", action="Updated", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Product content section updated", metadata={"product_id": section.product_id, "section_type": section.section_type}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, section), commit=True)

        return self.normalize_return(section, "Product content section updated successfully")

    def delete_product_content_section(self, section_id: int, token):
        user = self.user_service.get_user_from_token(token)

        section = self.db.query(ProductContentSection).filter(
            ProductContentSection.id == section_id,
            ProductContentSection.is_active == True
        ).first()

        if not section:
            return self.normalize_return(message="Product content section not found")

        previous_values = self.activity_log_service.snapshot(section, ["is_active"])
        section.is_active = False
        section.updated_by = user.id

        self.db.commit()
        self.activity_log_service.record(module="Product Content", action="Deleted", record_id=section.id, record_name=section.heading or f"Section #{section.id}", user=user, description="Product content section deactivated", metadata={"product_id": section.product_id}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, section), commit=True)

        return self.normalize_return(message="Product content section deleted successfully")


def get_product_content_section_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> ProductContentSectionService:
    return ProductContentSectionService(db, user_service, activity_log_service)
