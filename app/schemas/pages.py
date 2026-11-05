from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PageCreate(BaseModel):
    title: str
    slug: str
    page_type: str = "generic"
    status: str = "published"


class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    page_type: Optional[str] = None
    status: Optional[str] = None


class PageRead(BaseModel):
    id: int
    title: str
    slug: str
    page_type: str
    status: str
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


class PageContentResponse(BaseModel):
    page: dict
    sections: list[dict]
