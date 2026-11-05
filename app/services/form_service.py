from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.forms import Form
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.query import get_or_404


class FormService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service


    def get_all_forms(self, token: str):

        self.user_service.get_user_from_token(token)

        return self.db.query(Form).order_by(Form.id.asc()).all()


    def get_form(self, form_id: int, token: str):

        self.user_service.get_user_from_token(token)

        return get_or_404(self.db, Form, form_id, "Form not found")


    def update_form(self, form_id: int, form_data, token: str):

        user = self.user_service.get_user_from_token(token)

        form = get_or_404(self.db, Form, form_id, "Form not found")

        previous_values = self.activity_log_service.snapshot(form)
        if form_data.title is not None:
            form.title = form_data.title

        if form_data.form_type is not None:
            form.form_type = form_data.form_type

        if form_data.recipient_email is not None:
            form.recipient_email = form_data.recipient_email

        if form_data.cc_email is not None:
            form.cc_email = form_data.cc_email

        if form_data.auto_reply_enabled is not None:
            form.auto_reply_enabled = form_data.auto_reply_enabled

        if form_data.auto_reply_subject is not None:
            form.auto_reply_subject = form_data.auto_reply_subject

        if form_data.auto_reply_message is not None:
            form.auto_reply_message = form_data.auto_reply_message

        self.db.commit()
        self.db.refresh(form)
        self.activity_log_service.record(module="Forms", action="Updated", record_id=form.id, record_name=form.title, user=user, description="Form updated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, form), commit=True)

        return {"message": "Form updated successfully"}

   

    def set_form_status(self, form_id: int, status_data, token: str):

        user = self.user_service.get_user_from_token(token)

        form = get_or_404(self.db, Form, form_id, "Form not found")

        previous_values = self.activity_log_service.snapshot(form, ["is_active"])
        form.is_active = bool(status_data.is_active)

        self.db.commit()
        self.db.refresh(form)
        self.activity_log_service.record(module="Forms", action="Activated" if form.is_active else "Deactivated", record_id=form.id, record_name=form.title, user=user, description="Form status changed", metadata={"is_active": form.is_active}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, form), commit=True)

        return {
            "message": f"Form {'activated' if form.is_active else 'deactivated'} successfully"
        }


def get_form_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> FormService:
    return FormService(db, user_service, activity_log_service)
