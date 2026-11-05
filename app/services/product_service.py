from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.media import Media
from app.models.product_categories import ProductCategory
from app.models.product_content_sections import ProductContentSection
from app.models.products import Product
from app.models.product_industry_tags import IndustryTag
from app.models.seo import SEO
from app.schemas.products import ProductCreate, ProductUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now
from app.utils.query import get_or_404
from app.utils.text import clean_html_content, clean_product_text


PRODUCT_REFERENCE_TYPE = "product"
PRODUCT_WRITE_FIELDS = [
    "page_id",
    "title",
    "slug",
    "short_description",
    "category_id",
    "featured_image_id",
    "datasheet_file_id",
    "video_file_id",
    "youtube_url",
    "specifications",
    "status",
    "display_order",
    "is_active",
]
PRODUCT_RELATION_FIELDS = ["sections", "faqs", "seo", "industry_tag_ids"]


class ProductService:
    def __init__(
        self,
        db,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def _serialize_date(self, value):
        return format_datetime_ist(value) if value else None

    def _clean_text(self, value):
        return clean_html_content(value) if isinstance(value, str) and "<" in value else clean_product_text(value)

    def _clean_specifications(self, specifications):
        if not specifications:
            return specifications
        if isinstance(specifications, list):
            cleaned = []
            for item in specifications:
                if not isinstance(item, dict):
                    cleaned.append(item)
                    continue
                cleaned.append({
                    **item,
                    "name": self._clean_text(item.get("name")) if item.get("name") is not None else item.get("name"),
                    "value": self._clean_text(item.get("value")) if item.get("value") is not None else item.get("value"),
                })
            return cleaned
        if isinstance(specifications, dict):
            return {self._clean_text(str(name)): self._clean_text(str(value)) for name, value in specifications.items()}
        return specifications

    def _prepare_write_values(self, values: dict):
        prepared = dict(values)
        if "short_description" in prepared:
            prepared["short_description"] = self._clean_text(prepared["short_description"])
        if "specifications" in prepared:
            prepared["specifications"] = self._clean_specifications(prepared["specifications"])
        if "title" in prepared and prepared["title"] is not None:
            prepared["title"] = self._clean_text(prepared["title"])
        return prepared

    def _serialize_media(self, media_id, media_map=None):
        if media_id is None:
            return None

        media = media_map.get(media_id) if media_map is not None else self.db.query(Media).filter(Media.id == media_id).first()
        if not media:
            return None

        return {
            "id": media.id,
            "file_name": media.file_name,
            "url": media.url,
            "mime_type": media.mime_type,
            "alt_text": media.alt_text,
        }

    def _media_map_for_ids(self, media_ids):
        ids = {media_id for media_id in media_ids if media_id}
        if not ids:
            return {}
        return {media.id: media for media in self.db.query(Media).filter(Media.id.in_(ids)).all()}

    def _serialize_category(self, category):
        if not category:
            return None

        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "is_active": bool(category.is_active),
        }

    def _serialize_content_section(self, section):
        return {
            "id": section.id,
            "product_id": section.product_id,
            "section_order": section.section_order,
            "section_type": section.section_type,
            "heading": section.heading,
            "content": section.content,
            "is_active": bool(section.is_active),
        }

    def _serialize_section(self, section):
        content = section.content
        if isinstance(content, dict):
            content = content.get("html")

        return {
            "id": section.id,
            "title": section.heading,
            "content": content,
            "sort_order": section.section_order,
            "is_active": bool(section.is_active),
        }

    def _serialize_faq(self, section):
        answer = section.content
        if isinstance(answer, dict):
            answer = answer.get("answer")

        return {
            "id": section.id,
            "question": section.heading,
            "answer": answer,
            "sort_order": section.section_order,
            "is_active": bool(section.is_active),
        }

    def _serialize_seo(self, seo):
        if not seo:
            return None

        return {
            "id": seo.id,
            "reference_type": seo.reference_type,
            "reference_id": seo.reference_id,
            "meta_title": seo.meta_title,
            "meta_description": seo.meta_description,
            "canonical_url": seo.canonical_url,
            "og_title": seo.og_title,
            "og_description": seo.og_description,
            "og_image_id": seo.og_image_id,
            "og_image_url": (self._serialize_media(seo.og_image_id) or {}).get("url"),
            "target_keywords": seo.target_keywords,
            "is_active": bool(seo.is_active),
            "created_at": self._serialize_date(seo.created_at),
            "created_by": seo.created_by,
            "updated_at": self._serialize_date(seo.updated_at),
            "updated_by": seo.updated_by,
        }

    def _serialize_specifications(self, specifications):
        if not specifications:
            return []

        if isinstance(specifications, dict):
            return [
                {"name": str(name), "value": str(value)}
                for name, value in specifications.items()
            ]

        if not isinstance(specifications, list):
            return []

        normalized = []
        for item in specifications:
            if not isinstance(item, dict):
                continue

            name = item.get("name", item.get("label"))
            value = item.get("value")
            if name is None or value is None:
                continue

            normalized.append({"name": str(name), "value": str(value)})

        return normalized

    def _serialize_industry_tag(self, tag):
        if not tag:
            return None

        industry_tag = (
            self.db.query(IndustryTag)
            .filter(IndustryTag.id == tag)
            .first()
        )

        if not industry_tag:
            return None

        return {
            "id": industry_tag.id,
            "name": industry_tag.name,
            "is_active": bool(industry_tag.is_active),
        }

    def _serialize_detail(self, product):
        category = self.db.query(ProductCategory).filter(ProductCategory.id == product.category_id).first()
        content_sections = (
            self.db.query(ProductContentSection)
            .filter(ProductContentSection.product_id == product.id)
            .order_by(ProductContentSection.section_order.asc())
            .all()
        )
        sections = [section for section in content_sections if section.section_type != "faq"]
        faqs = [section for section in content_sections if section.section_type == "faq"]
        seo = (
            self.db.query(SEO)
            .filter(SEO.reference_type == PRODUCT_REFERENCE_TYPE, SEO.reference_id == product.id)
            .first()
        )
        
        industry_tags = [
                self._serialize_industry_tag(tag)
                for tag in (product.industry_tag_id or [])
            ]

        return {
            "id": product.id,
            "title": product.title,
            "slug": product.slug,
            "short_description": product.short_description,
            "category": self._serialize_category(category),
            "featured_image_id": product.featured_image_id,
            "featured_image": self._serialize_media(product.featured_image_id),
            "datasheet_file_id": product.datasheet_file_id,
            "datasheet": self._serialize_media(product.datasheet_file_id),
            "video_file_id": product.video_file_id,
            "video": self._serialize_media(product.video_file_id),
            "youtube_url": product.youtube_url,
            "specifications": self._serialize_specifications(product.specifications),
            "industry_tag_id": industry_tags ,
            "content_sections": [self._serialize_content_section(section) for section in content_sections],
            "sections": [self._serialize_section(section) for section in sections],
            "faqs": [self._serialize_faq(faq) for faq in faqs],
            "seo": self._serialize_seo(seo),
            "status": product.status,
            "display_order": product.display_order,
        }

    def _serialize_list_item(self, product, category_name=None):
        return {
            "id": product.id,
            "title": product.title,
            "slug": product.slug,
            "category_name": category_name,
            "status": product.status,
            "display_order": product.display_order,
            "is_active": bool(product.is_active),
            "created_at": self._serialize_date(product.created_at),
        }

    def _validate_category(self, category_id):
        category = self.db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Product category not found")

    def _validate_media_ids(self, product_data):
        media_fields = [
            "featured_image_id",
            "datasheet_file_id",
            "video_file_id",
        ]

        values = []
        for field_name in media_fields:
            if hasattr(product_data, field_name):
                value = getattr(product_data, field_name)
                if value is not None:
                    values.append(value)

        if not values:
            return

        existing_count = self.db.query(Media).filter(Media.id.in_(values)).count()
        if existing_count != len(set(values)):
            raise HTTPException(status_code=404, detail="One or more media files were not found")

    def _validate_industry_tags(self, industry_tag_ids):
        if not industry_tag_ids:
            return

        tags = self.db.query(IndustryTag).filter(
            IndustryTag.id.in_(industry_tag_ids),
            IndustryTag.is_active == True
        ).all()

        found_ids = {tag.id for tag in tags}
        missing_ids = set(industry_tag_ids) - found_ids

        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Industry tags not found: {missing_ids}"
            )

    def _set_product_industry_tags(self, product: Product, industry_tag_ids):
       
        if industry_tag_ids is None:
            return

        # Ensure all IDs exist and are active
        self._validate_industry_tags(industry_tag_ids)

        # Store the list directly in the JSON column
        product.industry_tag_id = industry_tag_ids

    def _ensure_slug_available(self, slug, exclude_product_id=None):
        from app.utils.query import ensure_slug_available
        ensure_slug_available(
            self.db, Product, slug, exclude_id=exclude_product_id, detail="Product with this slug already exists"
        )

    def _validate_youtube_url(self, url: str):
        if not url:
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    def _create_product_sections(self, product_id: int, sections, user_id: int):
        if sections is None:
            return

        for section_data in sections:
            self.db.add(
                ProductContentSection(
                    product_id=product_id,
                    section_order=section_data.sort_order,
                    section_type="paragraph",
                    heading=clean_product_text(section_data.title),
                    content={"html": clean_html_content(section_data.content)},
                    is_active=section_data.is_active,
                    created_by=user_id,
                    updated_by=user_id,
                )
            )

    def _create_product_faqs(self, product_id: int, faqs, user_id: int):
        if faqs is None:
            return

        for faq_data in faqs:
            self.db.add(
                ProductContentSection(
                    product_id=product_id,
                    section_order=faq_data.sort_order,
                    section_type="faq",
                    heading=clean_product_text(faq_data.question),
                    content={"answer": clean_product_text(faq_data.answer)},
                    is_active=faq_data.is_active,
                    created_by=user_id,
                    updated_by=user_id,
                )
            )

    def _replace_product_sections(self, product_id: int, sections, user_id: int):
        if sections is None:
            return

        self.db.query(ProductContentSection).filter(
            ProductContentSection.product_id == product_id,
            ProductContentSection.section_type != "faq",
        ).delete(synchronize_session=False)
        self._create_product_sections(product_id, sections, user_id)

    def _replace_product_faqs(self, product_id: int, faqs, user_id: int):
        if faqs is None:
            return

        self.db.query(ProductContentSection).filter(
            ProductContentSection.product_id == product_id,
            ProductContentSection.section_type == "faq",
        ).delete(synchronize_session=False)
        self._create_product_faqs(product_id, faqs, user_id)

    def _upsert_product_seo(self, product: Product, seo_data, user_id: int):
        seo = (
            self.db.query(SEO)
            .filter(SEO.reference_type == PRODUCT_REFERENCE_TYPE, SEO.reference_id == product.id)
            .first()
        )

        if not seo:
            seo = SEO(
                reference_type=PRODUCT_REFERENCE_TYPE,
                reference_id=product.id,
                created_by=user_id,
            )
            self.db.add(seo)

        if seo_data is None:
            if not seo.meta_title:
                seo.meta_title = product.title
            seo.is_active = True
        else:
            seo.meta_title = self._clean_text(seo_data.meta_title)
            seo.meta_description = self._clean_text(seo_data.meta_description)
            seo.canonical_url = seo_data.canonical_url
            seo.og_title = self._clean_text(seo_data.og_title)
            seo.og_description = self._clean_text(seo_data.og_description)
            if "og_image_id" in seo_data.model_fields_set:
                seo.og_image_id = seo_data.og_image_id
            seo.target_keywords = seo_data.target_keywords
            seo.is_active = seo_data.is_active

        seo.updated_by = user_id

    def get_all_products(self, token):
        self.user_service.get_user_from_token(token)

        products = (
            self.db.query(Product, ProductCategory.name.label("category_name"))
            .join(ProductCategory, Product.category_id == ProductCategory.id)
            .order_by(Product.is_active.desc(), ProductCategory.name.asc(), Product.id.asc())
            .all()
        )

        media_map = self._media_map_for_ids(
            [product.featured_image_id for product, _ in products]
        )

        product_dict = {}
        for product, category_name in products:
            if category_name not in product_dict:
                product_dict[category_name] = {
                    "launched": [],
                    "upcoming": []
                }

            product_data = {
                "product_id": product.id,
                "product_name": product.title,
                "slug": product.slug,
                "featured_image": self._serialize_media(product.featured_image_id, media_map),
                "category_name": category_name,
                "status": product.status,
                "is_active": product.is_active,
            }

            if product.status == "launched":
                product_dict[category_name]["launched"].append(product_data)
            else:
                product_dict[category_name]["upcoming"].append(product_data)

        return product_dict

    def get_product(self, product_id: int, token):
        self.user_service.get_user_from_token(token)
        product = get_or_404(self.db, Product, product_id, "Product not found")
        return self._serialize_detail(product)

    def create_product(self, product_data: ProductCreate, token):
        user = self.user_service.get_user_from_token(token)
        self._ensure_slug_available(product_data.slug)
        self._validate_category(product_data.category_id)
        self._validate_media_ids(product_data)
        self._validate_youtube_url(product_data.youtube_url)
        self._validate_industry_tags(product_data.industry_tag_ids)

        try:
            product_values = self._prepare_write_values(
                product_data.model_dump(mode="json", exclude=set(PRODUCT_RELATION_FIELDS))
            )
            product = Product(
                **product_values,
                created_by=user.id,
                updated_by=user.id,
            )

            self.db.add(product)
            self.db.flush()

            self._create_product_sections(product.id, product_data.sections, user.id)
            self._create_product_faqs(product.id, product_data.faqs, user.id)
            self._set_product_industry_tags(product, product_data.industry_tag_ids)

            self._upsert_product_seo(product, product_data.seo, user.id)
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise

        self.activity_log_service.record(
            module="Products",
            action="Added",
            record_id=product.id,
            record_name=product.title,
            user=user,
            description="Product created",
            commit=True,
        )

        return {"message": "Product created successfully", "product_id": product.id}

    def update_product(self, product_id: int, product_data: ProductUpdate, token):
        user = self.user_service.get_user_from_token(token)
        product = get_or_404(self.db, Product, product_id, "Product not found")

        previous_values = self.activity_log_service.snapshot(product)
        update_data = self._prepare_write_values(
            product_data.model_dump(exclude_unset=True, mode="json", exclude=set(PRODUCT_RELATION_FIELDS))
        )
        if "slug" in update_data:
            self._ensure_slug_available(update_data["slug"], exclude_product_id=product.id)

        if "category_id" in update_data:
            self._validate_category(update_data["category_id"])

        self._validate_media_ids(product_data)
        if "youtube_url" in update_data:
            self._validate_youtube_url(update_data["youtube_url"])

        if product_data.industry_tag_ids is not None:
            self._validate_industry_tags(product_data.industry_tag_ids)

        try:
            for field_name in PRODUCT_WRITE_FIELDS:
                if field_name in update_data:
                    setattr(product, field_name, update_data[field_name])

            if product_data.sections is not None:
                self._replace_product_sections(product.id, product_data.sections, user.id)

            if product_data.faqs is not None:
                self._replace_product_faqs(product.id, product_data.faqs, user.id)

            if product_data.industry_tag_ids is not None:
                self._set_product_industry_tags(product, product_data.industry_tag_ids)

            if product_data.seo is not None:
                self._upsert_product_seo(product, product_data.seo, user.id)

            product.updated_by = user.id
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise

        self.activity_log_service.record(
            module="Products",
            action="Updated",
            record_id=product.id,
            record_name=product.title,
            user=user,
            description="Product updated",
            metadata={"fields": list(update_data.keys())},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, product),
            commit=True,
        )

        return {"message": "Product updated successfully", "product_id": product.id}

    def set_product_status(self, product_id: int, is_active: bool, token):
        user = self.user_service.get_user_from_token(token)
        product = get_or_404(self.db, Product, product_id, "Product not found")

        previous_values = self.activity_log_service.snapshot(product, ["is_active"])
        product.is_active = bool(is_active)
        product.updated_by = user.id
        self.db.commit()
        self.db.refresh(product)
        self.activity_log_service.record(
            module="Products",
            action="Activated" if product.is_active else "Deactivated",
            record_id=product.id,
            record_name=product.title,
            user=user,
            description="Product status changed",
            metadata={"is_active": product.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, product),
            commit=True,
        )

        return {
            "message": f"Product {'activated' if product.is_active else 'deactivated'} successfully",
            "product_id": product.id,
            "is_active": product.is_active,
        }


def get_product_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> ProductService:
    return ProductService(db, user_service, activity_log_service)
