from typing import Optional

from pydantic import BaseModel, Field


class MenuCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    icon: Optional[str] = Field(default=None, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class MenuUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    icon: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = Field(default=None, ge=0)

