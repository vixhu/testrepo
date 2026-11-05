from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.department_contact import DepartmentContact
from app.schemas.department_contact import DepartmentContactCreate, DepartmentContactStatusUpdate, DepartmentContactUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


class DepartmentContactService:
    def __init__(self, db: Session, user_service: UserService, activity_log_service: ActivityLogService):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def get_department_contacts(self, token) -> List[DepartmentContact]:
        self.user_service.get_user_from_token(token)
        return self.db.query(DepartmentContact).order_by(DepartmentContact.display_order).all()

    def get_department_contact(self, department_contact_id: int, token):
        self.user_service.get_user_from_token(token)
        department_contact = self.db.query(DepartmentContact).filter(DepartmentContact.id == department_contact_id).first()

        if not department_contact:
            raise HTTPException(status_code=404, detail="Department contact not found")

        return department_contact

    def create_department_contact(self, department_contact_data: DepartmentContactCreate, token):
        user = self.user_service.get_user_from_token(token)
        department_contact = DepartmentContact(**department_contact_data.model_dump(), created_by=user.id)

        self.db.add(department_contact)
        self.db.commit()
        self.db.refresh(department_contact)

        self.activity_log_service.record(
            module="Department Contacts",
            action="Created",
            record_id=department_contact.id,
            record_name=department_contact.department_name,
            user=user,
            description="Department contact created",
            metadata={"department_name": department_contact.department_name},
            commit=True,
        )

        return department_contact

    def update_department_contact(self, department_contact_id: int, department_contact_data: DepartmentContactUpdate, token):
        user = self.user_service.get_user_from_token(token)
        department_contact = self.db.query(DepartmentContact).filter(DepartmentContact.id == department_contact_id).first()

        if not department_contact:
            raise HTTPException(status_code=404, detail="Department contact not found")

        previous_values = self.activity_log_service.snapshot(department_contact)

        for key, value in department_contact_data.model_dump(exclude_unset=True).items():
            setattr(department_contact, key, value)

        department_contact.updated_by = user.id

        self.db.commit()
        self.db.refresh(department_contact)

        self.activity_log_service.record(
            module="Department Contacts",
            action="Updated",
            record_id=department_contact.id,
            record_name=department_contact.department_name,
            user=user,
            description="Department contact updated",
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, department_contact),
            commit=True,
        )

        return department_contact

    def set_department_contact_status(self, department_contact_id: int, status_data: DepartmentContactStatusUpdate, token):
        user = self.user_service.get_user_from_token(token)
        department_contact = self.db.query(DepartmentContact).filter(DepartmentContact.id == department_contact_id).first()

        if not department_contact:
            raise HTTPException(status_code=404, detail="Department contact not found")

        previous_values = self.activity_log_service.snapshot(department_contact, ["is_active"])

        department_contact.is_active = status_data.is_active
        department_contact.updated_by = user.id

        self.db.commit()
        self.db.refresh(department_contact)

        self.activity_log_service.record(
            module="Department Contacts",
            action="Activated" if department_contact.is_active else "Deactivated",
            record_id=department_contact.id,
            record_name=department_contact.department_name,
            user=user,
            description="Department contact status changed",
            metadata={"is_active": department_contact.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, department_contact),
            commit=True,
        )

        return department_contact


def get_department_contact_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)):

    return DepartmentContactService(db, user_service, activity_log_service)