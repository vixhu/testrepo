from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.media import Media
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.files import (
    MAX_IMAGE_SIZE,
    MAX_PDF_SIZE,
    MAX_VIDEO_SIZE,
    PDF_TYPE,
    alt_text_for_upload,
    cloudinary_folder,
    public_id_from_name,
    sanitize_filename,
    upload_to_cloudinary,
)

MEDIA_KINDS = {
    "image": {"folder": "images", "allowed_types": {"image/webp"}, "label": "image", "max_size": MAX_IMAGE_SIZE},
    "video": {"folder": "videos", "allowed_types": {"video/webm"}, "label": "video", "max_size": MAX_VIDEO_SIZE},
    "datasheet": {"folder": "datasheets", "allowed_types": {PDF_TYPE}, "label": "datasheet", "max_size": MAX_PDF_SIZE},
}


class ProductMediaService:
    def __init__(
        self,
        db: Session,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def upload_media(self, upload_file: UploadFile, product_name: str, media_type: str, token: str):
        user = self.user_service.get_user_from_token(token)
        kind = (media_type or "image").strip().lower()
        if kind not in MEDIA_KINDS:
            raise HTTPException(status_code=400, detail="media_type must be image, video, or datasheet")

        spec = MEDIA_KINDS[kind]
        original_name = upload_file.filename or "uploaded_file"
        stem = public_id_from_name(original_name)
        filename = sanitize_filename(original_name)
        product_folder = product_name.strip() if product_name and product_name.strip() else "unassigned"
        folder_path = cloudinary_folder("products", product_folder, spec["folder"])

        result = upload_to_cloudinary(
            upload_file,
            folder_path,
            public_id=stem,
            unique_public_id=False,
            allowed_types=spec["allowed_types"],
            max_size=spec["max_size"],
        )
        media_url = result["url"]

        alt_context = None
        if product_name and product_name.strip().lower() != "unassigned":
            suffix = " datasheet" if kind == "datasheet" else f" {spec['label']}" if kind != "image" else ""
            alt_context = f"{product_name.strip()}{suffix}"
        elif kind == "datasheet":
            alt_context = "Product datasheet"
        elif kind == "video":
            alt_context = "Product video"
        alt_text = alt_text_for_upload(original_name, alt_context)

        media_record = self._existing_product_media(folder_path, stem)
        if media_record:
            media_record.file_name = result["file_name"]
            media_record.url = media_url
            media_record.mime_type = upload_file.content_type
            media_record.alt_text = alt_text
            media_record.updated_by = user.id
        else:
            media_record = Media(
                file_name=result["file_name"],
                url=media_url,
                mime_type=upload_file.content_type,
                alt_text=alt_text,
                created_by=user.id,
                updated_by=user.id,
            )
            self.db.add(media_record)

        self.db.commit()
        self.db.refresh(media_record)
        self.activity_log_service.record(module="Media", action="Uploaded", record_id=media_record.id, record_name=filename, user=user, description="Product media uploaded", metadata={"mime_type": upload_file.content_type}, commit=True)

        return {
            "id": media_record.id,
            "file_name": result["file_name"],
            "url": media_url,
            "mime_type": upload_file.content_type,
            "alt_text": alt_text,
        }

    def _existing_product_media(self, folder_path: str, stem: str):
        marker = f"{folder_path}/{stem}"
        return (
            self.db.query(Media)
            .filter(Media.url.like(f"%{marker}%"))
            .order_by(Media.id.asc())
            .first()
        )


def get_product_media_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> ProductMediaService:
    return ProductMediaService(db, user_service, activity_log_service)
