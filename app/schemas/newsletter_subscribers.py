from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime, timezone
import zoneinfo

class NewsletterSubscriberBase(BaseModel):
    email: EmailStr
    is_active: bool

class NewsletterSubscriberCreate(NewsletterSubscriberBase):
    pass

class NewsletterSubscriberResponse(NewsletterSubscriberBase):
    id: int
    created_at: datetime
    
    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist = zoneinfo.ZoneInfo("Asia/Kolkata")
        return dt.astimezone(ist).isoformat()

    class Config:
        from_attributes = True

class PaginatedNewsletterSubscriberResponse(BaseModel):
    data: List[NewsletterSubscriberResponse]
    total: int
    page: int
    limit: int
