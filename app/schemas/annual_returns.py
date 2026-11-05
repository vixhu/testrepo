from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnnualReturnBase(BaseModel):
    title: str
    pdf_file_url: Optional[str] = None
    is_active: Optional[bool] = True

class AnnualReturnCreate(AnnualReturnBase):
    pass

class AnnualReturnUpdate(BaseModel):
    title: Optional[str] = None
    pdf_file_url: Optional[str] = None
    is_active: Optional[bool] = None

class AnnualReturnStatusUpdate(BaseModel):
    is_active: bool

class AnnualReturnResponse(AnnualReturnBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AnnualReturnListResponse(BaseModel):
    success: bool = True
    data: list[AnnualReturnResponse]
    pagination: dict

class AnnualReturnDetailResponse(BaseModel):
    success: bool = True
    data: AnnualReturnResponse

class AnnualReturnCreateResponse(BaseModel):
    success: bool = True
    message: str
    data: dict  # {"id": int}
