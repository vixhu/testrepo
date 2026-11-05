from typing import Any, Optional

from pydantic import BaseModel


class ProductContentSectionCreate(BaseModel):
    product_id: int
    section_order: int = 1
    section_type: str
    heading: Optional[str] = None
    content: Optional[Any] = None


class ProductContentSectionUpdate(BaseModel):
    product_id: Optional[int] = None
    section_order: Optional[int] = None
    section_type: Optional[str] = None
    heading: Optional[str] = None
    content: Optional[Any] = None
