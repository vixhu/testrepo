from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.catalogues import Catalogue
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.files import PDF_TYPE, cloudinary_folder, upload_to_cloudinary
from app.utils.pagination import paginate_query
from app.utils.query import get_or_404


class CatalogueService:

    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):

        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service


    def get_all_catalogues(self, token: str, page: int | None = None, limit: int | None = None):
        self.user_service.get_user_from_token(token)
        query = self.db.query(Catalogue).order_by(Catalogue.id.asc())
        items, meta = paginate_query(query, page, limit)
        if meta is None:
            return items
        return {"data": items, **meta}


    def get_catalogue(self, catalogue_id: int, token: str):

        self.user_service.get_user_from_token(token)
        return get_or_404(self.db, Catalogue, catalogue_id, "Catalogue not found")


    def create_catalogue(self, catalogue_data, token: str):

        user = self.user_service.get_user_from_token(token)

        catalogue = Catalogue(
            title=catalogue_data.title,
            pdf_url=catalogue_data.pdf_url,
            is_active=catalogue_data.is_active,
            created_by=user.id,
        )

        self.db.add(catalogue)
        self.db.commit()
        self.db.refresh(catalogue)
        self.activity_log_service.record(module="Catalogues", action="Added", record_id=catalogue.id, record_name=catalogue.title, user=user, description="Catalogue created", commit=True)

        return {
            "message": "Catalogue created successfully",
            "id": catalogue.id
        }


    def update_catalogue(self, catalogue_id: int, catalogue_data, token: str):

        user = self.user_service.get_user_from_token(token)

        catalogue = get_or_404(self.db, Catalogue, catalogue_id, "Catalogue not found")

        previous_values = self.activity_log_service.snapshot(catalogue)
        if catalogue_data.title is not None:
            catalogue.title = catalogue_data.title

        if catalogue_data.pdf_url is not None:
            catalogue.pdf_url = catalogue_data.pdf_url

        if catalogue_data.is_active is not None:
            catalogue.is_active = catalogue_data.is_active

        catalogue.updated_by = user.id

        self.db.commit()
        self.db.refresh(catalogue)
        self.activity_log_service.record(module="Catalogues", action="Updated", record_id=catalogue.id, record_name=catalogue.title, user=user, description="Catalogue updated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, catalogue), commit=True)

        return {"message": "Catalogue updated successfully"}


    def upload_catalogue_file(self, upload_file, token: str):
        self.user_service.get_user_from_token(token)
        result = upload_to_cloudinary(upload_file, cloudinary_folder("catalogues", "pdfs"), allowed_types={PDF_TYPE})
        return {
            "url": result["url"],
            "file_name": result["file_name"],
            "mime_type": result["mime_type"],
        }

    def set_catalogue_status(self, catalogue_id: int, status_data, token: str):

        user = self.user_service.get_user_from_token(token)

        catalogue = get_or_404(self.db, Catalogue, catalogue_id, "Catalogue not found")

        previous_values = self.activity_log_service.snapshot(catalogue, ["is_active"])
        catalogue.is_active = bool(status_data.is_active)
        catalogue.updated_by = user.id

        self.db.commit()
        self.db.refresh(catalogue)
        self.activity_log_service.record(module="Catalogues", action="Activated" if catalogue.is_active else "Deactivated", record_id=catalogue.id, record_name=catalogue.title, user=user, description="Catalogue status changed", metadata={"is_active": catalogue.is_active}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, catalogue), commit=True)

        return {
            "message": f"Catalogue {'activated' if catalogue.is_active else 'deactivated'} successfully"
        }


def get_catalogue_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> CatalogueService:

    return CatalogueService(db, user_service, activity_log_service)
