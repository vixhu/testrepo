from typing import Optional
from pydantic import BaseModel, EmailStr


class FormUpdate(BaseModel):
    title: Optional[str] = None
    form_type: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    cc_email: Optional[EmailStr] = None
    auto_reply_enabled: Optional[bool] = None
    auto_reply_subject: Optional[str] = None
    auto_reply_message: Optional[str] = None


class FormResponse(BaseModel):
    id: int
    title: str
    form_type: str
    recipient_email: str
    cc_email: Optional[str]
    auto_reply_enabled: bool
    auto_reply_subject: Optional[str]
    auto_reply_message: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class FormStatusUpdate(BaseModel):
    is_active: bool
