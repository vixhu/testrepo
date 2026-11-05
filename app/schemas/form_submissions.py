from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr


FormSubmissionType = Literal["contact", "datasheet", "career", "catalogue", "general"]


class FormSubmissionCreate(BaseModel):
    form_id: Optional[int] = None
    form_type: FormSubmissionType
    product_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    location: Optional[str] = None
    attachment_url: Optional[str] = None


class FormSubmissionUpdate(BaseModel):
    form_id: Optional[int] = None
    form_type: Optional[FormSubmissionType] = None
    product_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    location: Optional[str] = None
    attachment_url: Optional[str] = None


class FormSubmissionFilter(BaseModel):
    page: int = 1
    limit: int = 20
    search: Optional[str] = None
    form_type: Optional[FormSubmissionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

