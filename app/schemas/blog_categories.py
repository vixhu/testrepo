from typing import Optional
from pydantic import BaseModel


class BlogCategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True

class BlogCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BlogCategoryStatusUpdate(BaseModel):
    is_active: bool

