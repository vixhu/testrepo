from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class BlogCreate(BaseModel):
    category_id: int
    title: str
    slug: str
    status: str = "draft"
    published_at: Optional[datetime] = None
    scheduled_publish_at: Optional[datetime] = None
    is_featured: bool = False
    author_name: Optional[str] = None
    author_image_url: Optional[str] = None


class BlogUpdate(BaseModel):
    blog_id: int
    category_id: int
    title: str
    slug: str
    status: str
    published_at: Optional[datetime] = None
    scheduled_publish_at: Optional[datetime] = None
    is_featured: bool = False
    author_name: Optional[str] = None
    author_image_url: Optional[str] = None
