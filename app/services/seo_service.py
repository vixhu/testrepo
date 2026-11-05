from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.media import Media
from app.models.seo import SEO
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now
from app.utils.files import CLOUDINARY_FOLDERS, IMAGE_TYPES, alt_text_for_upload, upload_to_cloudinary


class SeoService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service


    def _og_image_url(self, seo: SEO, url: str | None = None):
        if url is not None:
            return url
        if not seo.og_image_id:
            return None
        media = self.db.query(Media).filter(Media.id == seo.og_image_id).first()
        return media.url if media else None

    def _serialize_seo(self, seo: SEO, og_image_url: str | None = None):
        return {
            "id": seo.id,
            "reference_id": seo.reference_id,
            "reference_type": seo.reference_type,
            "meta_title": seo.meta_title,
            "meta_description": seo.meta_description,
            "canonical_url": seo.canonical_url,
            "og_title": seo.og_title,
            "og_description": seo.og_description,
            "og_image_id": seo.og_image_id,
            "og_image_url": self._og_image_url(seo, og_image_url),
            "target_keywords": seo.target_keywords,
            "is_active": seo.is_active,
            "created_at": format_datetime_ist(seo.created_at) if seo.created_at else None,
            "created_by": seo.created_by,
            "updated_at": format_datetime_ist(seo.updated_at) if seo.updated_at else None,
            "updated_by": seo.updated_by,
        }


    def get_all_seo(self, token):
        self.user_service.get_user_from_token(token)

        seo_records = (
            self.db.query(SEO, Media.url)
            .outerjoin(Media, Media.id == SEO.og_image_id)
            .order_by(SEO.is_active.desc(), SEO.id.asc())
            .all()
        )

        grouped_seo = {}
        for seo, og_image_url in seo_records:
            grouped_seo.setdefault(seo.reference_type, []).append(self._serialize_seo(seo, og_image_url))

        return grouped_seo
    
    def get_seo_by_id(self, seo_id: int, token):
        self.user_service.get_user_from_token(token)

        seo_record = (self.db.query(SEO).filter(SEO.id == seo_id, SEO.is_active == True).first())
        if not seo_record:
            raise HTTPException(status_code=404, detail="SEO record not found")

        return self._serialize_seo(seo_record)

    def update_seo(self, seo_id: int, update_seo, token):
        user = self.user_service.get_user_from_token(token)

        seo_record = (self.db.query(SEO).filter(SEO.id == seo_id, SEO.is_active == True).first())
        if not seo_record:
            raise HTTPException(status_code=404, detail="SEO record not found")

        previous_values = self.activity_log_service.snapshot(seo_record)


        if update_seo.meta_title is not None:
            seo_record.meta_title = update_seo.meta_title
        if update_seo.meta_description is not None:
            seo_record.meta_description = update_seo.meta_description
        if update_seo.canonical_url is not None:
            seo_record.canonical_url = update_seo.canonical_url
        if update_seo.og_title is not None:
            seo_record.og_title = update_seo.og_title
        if update_seo.og_description is not None:
            seo_record.og_description = update_seo.og_description
        if update_seo.og_image_id is not None:
            seo_record.og_image_id = update_seo.og_image_id
        if update_seo.target_keywords is not None:
            seo_record.target_keywords = update_seo.target_keywords

        seo_record.updated_by = user.id

        self.db.commit()
        self.db.refresh(seo_record)
        self.activity_log_service.record(module="SEO", action="Updated", record_id=seo_record.id, record_name=seo_record.meta_title or f"{seo_record.reference_type} #{seo_record.reference_id}", user=user, description="SEO metadata updated", metadata={"reference_type": seo_record.reference_type, "reference_id": seo_record.reference_id}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, seo_record), commit=True)

        return {
            "message": "SEO updated successfully",
            "seo_id": seo_record.id
        }

    def delete_seo(self, seo_id: int, token):
        user = self.user_service.get_user_from_token(token)

        if not seo_id:
            raise HTTPException(status_code=400, detail="SEO ID is required")

        seo_record = (self.db.query(SEO).filter(SEO.id == seo_id, SEO.is_active == True).first())
        if not seo_record:
            raise HTTPException(status_code=404, detail="SEO record not found")

        previous_values = self.activity_log_service.snapshot(seo_record, ["is_active"])
        seo_record.is_active = False
        seo_record.updated_by = user.id
       
        self.db.commit()
        self.db.refresh(seo_record)
        self.activity_log_service.record(module="SEO", action="Deleted", record_id=seo_record.id, record_name=seo_record.meta_title or f"{seo_record.reference_type} #{seo_record.reference_id}", user=user, description="SEO metadata deactivated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, seo_record), commit=True)

        return {
            "message": "SEO deleted successfully"
        }

    def activate_seo(self, seo_id: int, token):
        user = self.user_service.get_user_from_token(token)

        if not seo_id:
            raise HTTPException(status_code=400, detail="SEO ID is required")

        seo_record = self.db.query(SEO).filter(SEO.id == seo_id).first()
        if not seo_record:
            raise HTTPException(status_code=404, detail="SEO record not found")

        previous_values = self.activity_log_service.snapshot(seo_record, ["is_active"])
        seo_record.is_active = True
        seo_record.updated_by = user.id

        self.db.commit()
        self.db.refresh(seo_record)
        self.activity_log_service.record(module="SEO", action="Activated", record_id=seo_record.id, record_name=seo_record.meta_title or f"{seo_record.reference_type} #{seo_record.reference_id}", user=user, description="SEO metadata activated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, seo_record), commit=True)

        return {
            "message": "SEO activated successfully"
        }

    def upload_og_image(self, upload_file: UploadFile, token: str):
        user = self.user_service.get_user_from_token(token)
        result = upload_to_cloudinary(
            upload_file,
            CLOUDINARY_FOLDERS["seo-og"],
            allowed_types=IMAGE_TYPES,
        )

        media_record = Media(
            file_name=result["file_name"],
            url=result["url"],
            mime_type=result["mime_type"],
            alt_text=alt_text_for_upload(upload_file.filename or result["file_name"], "Open Graph image"),
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(media_record)
        self.db.commit()
        self.db.refresh(media_record)
        self.activity_log_service.record(
            module="SEO",
            action="Uploaded",
            record_id=media_record.id,
            record_name=result["file_name"],
            user=user,
            description="Open Graph image uploaded to Cloudinary",
            metadata={"mime_type": result["mime_type"], "url": result["url"]},
            commit=True,
        )

        return {
            "id": media_record.id,
            "url": result["url"],
            "file_name": result["file_name"],
            "mime_type": result["mime_type"],
            "alt_text": media_record.alt_text,
        }


def get_seo_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> SeoService:
    return SeoService(db, user_service, activity_log_service)
