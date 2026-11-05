from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.annual_returns import AnnualReturn
from app.schemas.annual_returns import AnnualReturnCreate, AnnualReturnUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.files import PDF_TYPE, cloudinary_folder, upload_to_cloudinary
from app.utils.pagination import paginate_query
from app.utils.query import get_or_404


class AnnualReturnService:

    def __init__(
        self,
        db: Session,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def get_all_annual_returns(self, token, page: int | None = None, limit: int | None = None):
        self.user_service.get_user_from_token(token)
        query = self.db.query(AnnualReturn)
        items, meta = paginate_query(query, page, limit)
        if meta is None:
            return items
        return {"data": items, **meta}


    def create_annual_return(self, annual_return: AnnualReturnCreate, token):
        user = self.user_service.get_user_from_token(token)
        db_annual_return = AnnualReturn(
            title=annual_return.title,
            pdf_file_url=annual_return.pdf_file_url,
            is_active=annual_return.is_active,
            created_by=user.id,
        )
        self.db.add(db_annual_return)
        self.db.commit()
        self.db.refresh(db_annual_return)

        self.activity_log_service.record(
            module="Annual Returns",
            action="Created",
            record_id=db_annual_return.id,
            record_name=db_annual_return.title,
            user=user,
            description="Annual return created",
            metadata={"title": db_annual_return.title},
            commit=True,
        )

        return {
            "message": "Annual return added successfully"
        }

    def update_annual_return(
        self,
        annual_return_id: int,
        annual_return_update: AnnualReturnUpdate,
        token) -> Optional[AnnualReturn]:
        user = self.user_service.get_user_from_token(token)
        db_annual_return = get_or_404(self.db, AnnualReturn, annual_return_id, "Annual return not found")

        previous_values = self.activity_log_service.snapshot(db_annual_return)

        for key, value in annual_return_update.model_dump(exclude_unset=True).items():
            setattr(db_annual_return, key, value)

        db_annual_return.updated_by = user.id
        self.db.commit()
        self.db.refresh(db_annual_return)

        self.activity_log_service.record(
            module="Annual Returns",
            action="Updated",
            record_id=db_annual_return.id,
            record_name=db_annual_return.title,
            user=user,
            description="Annual return updated",
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, db_annual_return),
            commit=True,
        )

        return {
            "message": "Annual return updated successfully"
        }

    def upload_annual_return_file(self, upload_file, token: str):
        self.user_service.get_user_from_token(token)
        result = upload_to_cloudinary(upload_file, cloudinary_folder("annual-returns", "pdfs"), allowed_types={PDF_TYPE})
        return {
            "url": result["url"],
            "file_name": result["file_name"],
            "mime_type": result["mime_type"],
            "label": "PDF",
        }

    def set_annual_return_status(self, annual_return_id: int, status_data, token) -> AnnualReturn:
        user = self.user_service.get_user_from_token(token)
        db_annual_return = get_or_404(self.db, AnnualReturn, annual_return_id, "Annual return not found")

        previous_values = self.activity_log_service.snapshot(db_annual_return, ["is_active"])

        db_annual_return.is_active = status_data.is_active
        db_annual_return.updated_by = user.id

        self.db.commit()
        self.db.refresh(db_annual_return)

        self.activity_log_service.record(
            module="Annual Returns",
            action="Activated" if db_annual_return.is_active else "Deactivated",
            record_id=db_annual_return.id,
            record_name=db_annual_return.title,
            user=user,
            description="Annual return status changed",
            metadata={"is_active": db_annual_return.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, db_annual_return),
            commit=True,
        )

        return db_annual_return


def get_annual_return_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> AnnualReturnService:

    return AnnualReturnService(db, user_service, activity_log_service)