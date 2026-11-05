from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.models.product_industry_tags import IndustryTag


ProductStatus = Literal["upcoming", "launched"]


class ProductSpecification(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)


class ProductSectionInput(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None
    sort_order: int = Field(default=1, ge=0)
    is_active: bool = True


class ProductFAQInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1)
    sort_order: int = Field(default=1, ge=0)
    is_active: bool = True


class ProductSEOInput(BaseModel):
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = Field(default=None, max_length=500)
    og_title: Optional[str] = Field(default=None, max_length=255)
    og_description: Optional[str] = None
    og_image_id: Optional[int] = None
    target_keywords: Optional[list[str]] = None
    is_active: bool = True


class ProductBase(BaseModel):
    page_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    short_description: Optional[str] = None
    category_id: int
    featured_image_id: Optional[int] = None
    datasheet_file_id: Optional[int] = None
    video_file_id: Optional[int] = None
    youtube_url: Optional[str] = Field(default=None, max_length=500)
    specifications: Optional[list[ProductSpecification]] = None
    industry_tag_ids: Optional[list[int]] = None
    status: ProductStatus = "upcoming"
    display_order: int = 0
    is_active: bool = True
    sections: Optional[list[ProductSectionInput]] = None
    faqs: Optional[list[ProductFAQInput]] = None
    seo: Optional[ProductSEOInput] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    page_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    short_description: Optional[str] = None
    category_id: Optional[int] = None
    featured_image_id: Optional[int] = None
    datasheet_file_id: Optional[int] = None
    video_file_id: Optional[int] = None
    youtube_url: Optional[str] = Field(default=None, max_length=500)
    specifications: Optional[list[ProductSpecification]] = None
    industry_tag_ids: Optional[list[int]] = None
    status: Optional[ProductStatus] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    sections: Optional[list[ProductSectionInput]] = None
    faqs: Optional[list[ProductFAQInput]] = None
    seo: Optional[ProductSEOInput] = None


class ProductQueryParams(BaseModel):
    page: int = 1
    limit: int = 20
    search: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    sort_by: str = "display_order"
    sort_order: Literal["asc", "desc"] = "asc"
