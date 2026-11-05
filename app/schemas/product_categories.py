from typing import Optional
from pydantic import BaseModel


class ProductCategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: int | None = None
    display_order: int = 0
    is_active: bool = True


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: int | None = None
    display_order: int
    is_active: Optional[bool] = None


class ProductCategoryStatusUpdate(BaseModel):
    is_active: bool

class CategoryTreeResponse(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int | None = None
    display_order: int
    is_active: bool
    children: list['CategoryTreeResponse'] = []

    class Config:
        from_attributes = True

CategoryTreeResponse.model_rebuild()
