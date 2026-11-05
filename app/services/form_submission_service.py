from math import ceil

from fastapi import Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.form_submissions import FormSubmission
from app.models.forms import Form
from app.models.products import Product
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist
from app.utils.excel import build_xlsx
from app.utils.query import get_or_404
from datetime import datetime

_UNSET = object()


class FormSubmissionService:
    def __init__(
        self,
        db,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def _related_maps(self, submissions):
        form_ids = {sub.form_id for sub in submissions if sub.form_id}
        product_ids = {sub.product_id for sub in submissions if sub.product_id}
        forms = {}
        products = {}
        if form_ids:
            forms = {form.id: form for form in self.db.query(Form).filter(Form.id.in_(form_ids)).all()}
        if product_ids:
            products = {product.id: product for product in self.db.query(Product).filter(Product.id.in_(product_ids)).all()}
        return forms, products

    def _serialize_submission(self, submission, form=_UNSET, product=_UNSET):
        if form is _UNSET:
            form = self.db.query(Form).filter(Form.id == submission.form_id).first() if submission.form_id else None
        if product is _UNSET:
            product = self.db.query(Product).filter(Product.id == submission.product_id).first() if submission.product_id else None
        return {
            "id": submission.id,
            "form_id": submission.form_id,
            "form": {
                "id": form.id,
                "title": form.title,
                "form_type": form.form_type,
            } if form else None,
            "form_type": submission.form_type,
            "product_id": submission.product_id,
            "product": {
                "id": product.id,
                "title": product.title,
                "slug": product.slug,
            } if product else None,
            "full_name": submission.full_name,
            "email": submission.email,
            "phone": submission.phone,
            "message": submission.message,
            "location": submission.location,
            "attachment_url": submission.attachment_url,
            "auto_reply_sent": submission.auto_reply_sent,
            "created_at": format_datetime_ist(submission.created_at, "%Y-%m-%dT%H:%M:%S+05:30") if submission.created_at else None,
            "created_by": submission.created_by,
            "updated_at": format_datetime_ist(submission.updated_at, "%Y-%m-%dT%H:%M:%S+05:30") if submission.updated_at else None,
            "updated_by": submission.updated_by,
        }

    def _ensure_form_exists(self, form_id: int):
        form = self.db.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form

    def _ensure_product_exists(self, product_id: int):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    def get_all_form_submissions(self, filter_data, token: str):
        self.user_service.get_user_from_token(token)
        query = self.db.query(FormSubmission)

        if filter_data.search:
            search = f"%{filter_data.search}%"
            query = query.filter(
                or_(
                    FormSubmission.full_name.ilike(search),
                    FormSubmission.email.ilike(search),
                    FormSubmission.phone.ilike(search),
                    FormSubmission.message.ilike(search),
                    FormSubmission.location.ilike(search),
                )
            )

        if filter_data.form_type:
            query = query.filter(FormSubmission.form_type == filter_data.form_type)

        if filter_data.start_date:
            query = query.filter(FormSubmission.created_at >= filter_data.start_date)
            
        if filter_data.end_date:
            query = query.filter(FormSubmission.created_at <= filter_data.end_date)

        query = query.order_by(FormSubmission.created_at.desc(), FormSubmission.id.desc())

        total = query.count()
        page = max(filter_data.page, 1)
        limit = min(max(filter_data.limit, 1), 100)
        submissions = query.offset((page - 1) * limit).limit(limit).all()
        forms, products = self._related_maps(submissions)

        return {
            "data": [
                self._serialize_submission(sub, forms.get(sub.form_id), products.get(sub.product_id))
                for sub in submissions
            ],
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": ceil(total / limit) if total else 0,
        }

    def export_form_submissions(self, token: str, form_type: str = None, start_date: datetime = None, end_date: datetime = None):
        user = self.user_service.get_user_from_token(token)
        
        query = self.db.query(FormSubmission)
        if form_type:
            query = query.filter(FormSubmission.form_type == form_type)
        if start_date:
            query = query.filter(FormSubmission.created_at >= start_date)
        if end_date:
            query = query.filter(FormSubmission.created_at <= end_date)
            
        submissions = query.order_by(FormSubmission.created_at.desc()).all()
        stream = build_xlsx(
            ["ID", "Form Type", "Full Name", "Email", "Phone", "Message", "Location", "Attachment URL", "Submitted At"],
            [
                [
                    sub.id,
                    sub.form_type,
                    sub.full_name or "",
                    sub.email or "",
                    sub.phone or "",
                    sub.message or "",
                    sub.location or "",
                    sub.attachment_url or "",
                    sub.created_at.strftime("%Y-%m-%d %H:%M:%S") if sub.created_at else "",
                ]
                for sub in submissions
            ],
            sheet_title="Form Submissions",
        )
        
        self.activity_log_service.record(
            module="Form Submissions",
            action="Exported",
            record_id=None,
            record_name="Form Submissions Export",
            user=user,
            description="Exported form submissions to Excel",
            metadata={
                "filters": {
                    "form_type": form_type,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "exported_count": len(submissions)
            },
            commit=True,
        )
        
        return stream

    def get_form_submission(self, submission_id: int, token: str):
        self.user_service.get_user_from_token(token)
        submission = get_or_404(self.db, FormSubmission, submission_id, "Form submission not found")
        return self._serialize_submission(submission)

    def create_form_submission(self, payload, token: str):
        user = self.user_service.get_user_from_token(token)

        if payload.form_id is not None:
            self._ensure_form_exists(payload.form_id)
        if payload.product_id is not None:
            self._ensure_product_exists(payload.product_id)

        submission = FormSubmission(
            form_id=payload.form_id,
            form_type=payload.form_type,
            product_id=payload.product_id,
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            message=payload.message,
            location=payload.location,
            attachment_url=payload.attachment_url,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        self.activity_log_service.record(module="Form Submissions", action="Added", record_id=submission.id, record_name=submission.full_name or submission.email or f"Submission #{submission.id}", user=user, description="Form submission created", metadata={"form_type": submission.form_type}, commit=True)

        return {
            "message": "Form submission created successfully",
            "form_submission": self._serialize_submission(submission),
        }

    def update_form_submission(self, submission_id: int, payload, token: str):
        user = self.user_service.get_user_from_token(token)
        submission = get_or_404(self.db, FormSubmission, submission_id, "Form submission not found")

        previous_values = self.activity_log_service.snapshot(submission)
        update_data = payload.model_dump(exclude_unset=True)
        if "form_id" in update_data and update_data["form_id"] is not None:
            self._ensure_form_exists(update_data["form_id"])
        if "product_id" in update_data and update_data["product_id"] is not None:
            self._ensure_product_exists(update_data["product_id"])

        for field_name, value in update_data.items():
            setattr(submission, field_name, value)

        submission.updated_by = user.id
        self.db.commit()
        self.db.refresh(submission)
        self.activity_log_service.record(module="Form Submissions", action="Updated", record_id=submission.id, record_name=submission.full_name or submission.email or f"Submission #{submission.id}", user=user, description="Form submission updated", metadata={"fields": list(update_data.keys())}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, submission), commit=True)

        return {
            "message": "Form submission updated successfully",
            "form_submission": self._serialize_submission(submission),
        }

    def delete_form_submission(self, submission_id: int, token: str):
        user = self.user_service.get_user_from_token(token)
        submission = get_or_404(self.db, FormSubmission, submission_id, "Form submission not found")

        record_name = submission.full_name or submission.email or f"Submission #{submission.id}"
        self.db.delete(submission)
        self.db.commit()
        self.activity_log_service.record(module="Form Submissions", action="Deleted", record_id=submission_id, record_name=record_name, user=user, description="Form submission deleted", commit=True)
        return {"message": "Form submission deleted successfully"}


def get_form_submission_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> FormSubmissionService:
    return FormSubmissionService(db, user_service, activity_log_service)
