from datetime import date, datetime
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.careers import Career
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now, today_ist
from app.utils.pagination import paginate_query

CAREER_FORM_ID = 5

def parse_closing_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])

class CareerService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):

        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def get_all_careers(self, token: str, page: int | None = None, limit: int | None = None):
        self.user_service.get_user_from_token(token)
        query = self.db.query(Career).order_by(Career.id.desc())
        items, meta = paginate_query(query, page, limit)
        if meta is None:
            return items
        return {"data": items, **meta}


    def get_career_by_id(self, career_id: int, token):

        self.user_service.get_user_from_token(token)

        career = self.db.query(Career).filter(Career.id == career_id).first()

        if not career:
            raise HTTPException(status_code=404, detail="Career not found")

        return career


    def create_career(self, career_data, token: str):

        user = self.user_service.get_user_from_token(token)

        career = Career(
            title=career_data.title,
            slug=career_data.slug,
            department=career_data.department,
            location=career_data.location,
            employment_type=career_data.employment_type,
            description=career_data.description,
            experience_min_years=career_data.experience_min_years,
            salary_min=career_data.salary_min,
            salary_max=career_data.salary_max,
            salary_currency=career_data.salary_currency,
            status=career_data.status,
            featured=career_data.featured,
            form_id = CAREER_FORM_ID,
            closing_date=parse_closing_date(career_data.closing_date),
            posted_at=get_utc_now(),
            created_by=user.id,
        )
        if career.closing_date and career.closing_date <= today_ist():
            career.is_active = False
            career.status = "closed"

        self.db.add(career)
        self.db.commit()
        self.db.refresh(career)
        self.activity_log_service.record(module="Careers", action="Added", record_id=career.id, record_name=career.title, user=user, description="Career created", metadata={"status": career.status}, commit=True)

        return {
            "message": "Career created successfully",
            "id": career.id
        }


    def update_career(self, career_id: int, career_data, token: str):

        user = self.user_service.get_user_from_token(token)

        career = self.db.query(Career).filter(Career.id == career_id, Career.is_active == True).first()

        if not career:
            raise HTTPException(status_code=404, detail="Career not found")

        previous_values = self.activity_log_service.snapshot(career)
        if career_data.title is not None:
            career.title = career_data.title

        if career_data.slug is not None:
            career.slug = career_data.slug

        if career_data.department is not None:
            career.department = career_data.department

        if career_data.location is not None:
            career.location = career_data.location

        if career_data.employment_type is not None:
            career.employment_type = career_data.employment_type

        if career_data.description is not None:
            career.description = career_data.description

        if career_data.experience_min_years is not None:
            career.experience_min_years = career_data.experience_min_years

        if career_data.salary_min is not None:
            career.salary_min = career_data.salary_min

        if career_data.salary_max is not None:
            career.salary_max = career_data.salary_max

        if career_data.salary_currency is not None:
            career.salary_currency = career_data.salary_currency

        if career_data.status is not None:
            career.status = career_data.status

        if career_data.featured is not None:
            career.featured = career_data.featured

        if career_data.closing_date is not None:
            career.closing_date = parse_closing_date(career_data.closing_date)
        if career.closing_date and career.closing_date <= today_ist():
            career.is_active = False
            career.status = "closed"

        career.updated_by = user.id

        self.db.commit()
        self.db.refresh(career)
        self.activity_log_service.record(module="Careers", action="Updated", record_id=career.id, record_name=career.title, user=user, description="Career updated", metadata={"status": career.status}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, career), commit=True)

        return {"message": "Career updated successfully"}


    def delete_career(self, career_id: int, token: str):

        user = self.user_service.get_user_from_token(token)

        career = self.db.query(Career).filter(Career.id == career_id).first()

        if not career:
            raise HTTPException(status_code=404, detail="Career not found")

        previous_values = self.activity_log_service.snapshot(career, ["is_active"])
        career.is_active = False

        self.db.commit()
        self.activity_log_service.record(module="Careers", action="Deleted", record_id=career.id, record_name=career.title, user=user, description="Career deleted", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, career), commit=True)

        return {"message": "Career deleted successfully"}


    def set_career_status(self, career_id: int, status_data, token: str):

        user = self.user_service.get_user_from_token(token)

        career = self.db.query(Career).filter(Career.id == career_id).first()

        if not career:
            raise HTTPException(status_code=404, detail="Career not found")

        previous_values = self.activity_log_service.snapshot(career, ["is_active"])
        career.is_active = bool(status_data.is_active)
        career.updated_by = user.id

        self.db.commit()
        self.db.refresh(career)
        self.activity_log_service.record(module="Careers", action="Activated" if career.is_active else "Deactivated", record_id=career.id, record_name=career.title, user=user, description="Career status changed", metadata={"is_active": career.is_active}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, career), commit=True)

        return {
            "message": f"Career {'activated' if career.is_active else 'deactivated'} successfully"
        }


def get_career_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> CareerService:

    return CareerService(db, user_service, activity_log_service)
