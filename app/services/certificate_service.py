from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.certificates import Certificate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.files import PDF_TYPE, cloudinary_folder, upload_to_cloudinary
from app.utils.pagination import paginate_query
from app.utils.query import get_or_404


class CertificateService:

    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):

        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service


    def get_all_certificates(self, token: str, page: int | None = None, limit: int | None = None):
        self.user_service.get_user_from_token(token)
        query = self.db.query(Certificate).order_by(Certificate.id.asc())
        items, meta = paginate_query(query, page, limit)
        if meta is None:
            return items
        return {"data": items, **meta}


    def get_certificate(self, certificate_id: int, token: str):

        self.user_service.get_user_from_token(token)
        return get_or_404(self.db, Certificate, certificate_id, "Certificate not found")


    def create_certificate(self, certificate_data, token: str):

        user = self.user_service.get_user_from_token(token)

        certificate = Certificate(
            title=certificate_data.title,
            issued_by=certificate_data.issued_by,
            issued_date=certificate_data.issued_date,
            expiry_date=certificate_data.expiry_date,
            pdf_url=certificate_data.pdf_url,
            is_active=certificate_data.is_active,
            created_by=user.id,
        )

        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        self.activity_log_service.record(
            module="Certificates",
            action="Added",
            record_id=certificate.id,
            record_name=certificate.title,
            user=user,
            description="Certificate created",
            commit=True,
        )

        return {
            "message": "Certificate created successfully",
            "id": certificate.id
        }


    def update_certificate(self, certificate_id: int, certificate_data, token: str):

        user = self.user_service.get_user_from_token(token)

        certificate = get_or_404(self.db, Certificate, certificate_id, "Certificate not found")

        previous_values = self.activity_log_service.snapshot(certificate)
        if certificate_data.title is not None:
            certificate.title = certificate_data.title

        if certificate_data.issued_by is not None:
            certificate.issued_by = certificate_data.issued_by

        if certificate_data.issued_date is not None:
            certificate.issued_date = certificate_data.issued_date

        if certificate_data.expiry_date is not None:
            certificate.expiry_date = certificate_data.expiry_date

        if certificate_data.pdf_url is not None:
            certificate.pdf_url = certificate_data.pdf_url

        if certificate_data.is_active is not None:
            certificate.is_active = certificate_data.is_active

        certificate.updated_by = user.id

        self.db.commit()
        self.db.refresh(certificate)
        self.activity_log_service.record(
            module="Certificates",
            action="Updated",
            record_id=certificate.id,
            record_name=certificate.title,
            user=user,
            description="Certificate updated",
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, certificate),
            commit=True,
        )

        return {"message": "Certificate updated successfully"}


    def upload_certificate_file(self, upload_file, token: str):
        self.user_service.get_user_from_token(token)
        result = upload_to_cloudinary(upload_file, cloudinary_folder("certificates", "pdfs"), allowed_types={PDF_TYPE})
        return {
            "url": result["url"],
            "file_name": result["file_name"],
            "mime_type": result["mime_type"],
        }

    def set_certificate_status(self, certificate_id: int, status_data, token: str):

        user = self.user_service.get_user_from_token(token)

        certificate = get_or_404(self.db, Certificate, certificate_id, "Certificate not found")

        previous_values = self.activity_log_service.snapshot(certificate, ["is_active"])
        certificate.is_active = bool(status_data.is_active)
        certificate.updated_by = user.id

        self.db.commit()
        self.db.refresh(certificate)
        self.activity_log_service.record(
            module="Certificates",
            action="Activated" if certificate.is_active else "Deactivated",
            record_id=certificate.id,
            record_name=certificate.title,
            user=user,
            description="Certificate status changed",
            metadata={"is_active": certificate.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, certificate),
            commit=True,
        )

        return {
            "message": f"Certificate {'activated' if certificate.is_active else 'deactivated'} successfully"
        }


def get_certificate_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> CertificateService:

    return CertificateService(db, user_service, activity_log_service)
